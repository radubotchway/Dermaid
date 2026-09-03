"""
Dermaid: held-out evaluation with train/test leakage detection.

Why this script exists
----------------------
train_model.py only ever pointed at train_set and took validation_split=0.2 from
it, so the 95.2% in the README is a model-selection split, not a generalisation
estimate. A real test_set shipped with the dataset and was never used.

But the test_set is NOT clean. The dataset was assembled from public sources and
passed through Roboflow, and a large fraction of test images also appear in
train_set: some byte-identical, many more as re-encoded or lightly augmented
copies. Evaluating on those images measures memorisation, not generalisation.

So this script does two things:

  1. Detects leakage by perceptual hash (16x16 average hash, 256 bits) between
     every test image and every train image.
  2. Reports metrics at several exclusion thresholds, so the effect of leakage
     on the headline number is visible rather than hidden.

The number to quote is the one at a threshold that excludes perceptual
duplicates. The raw number is reported only for comparison.

Metrics reported at each threshold:
  - per-class precision, recall, F1
  - macro F1, which weights every class equally regardless of size
  - majority-class baseline, so accuracy can be read in context
  - the condition-classified-as-clear-skin rate, the asymmetric error that
    matters clinically

Outputs evaluation_report.txt and confusion_matrix.png next to this script.

Usage:  python evaluate_heldout.py
"""

import os
import sys
from datetime import datetime

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from sklearn.metrics import classification_report, confusion_matrix
except ImportError:
    sys.exit("scikit-learn is not installed.\nActivate the venv and run:  pip install scikit-learn")

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))

DATASET_ROOT = r"C:\Users\ronar\Desktop\Programming\AI-Based Skin Disease Diagnosis Tool\Dataset\archive\skin-disease-datasaet"
TRAIN_DIR = os.path.join(DATASET_ROOT, "train_set")
TEST_DIR = os.path.join(DATASET_ROOT, "test_set")

WEIGHTS = os.path.join(HERE, "model.weights.h5")
CLASS_NAMES_FILE = os.path.join(HERE, "class_names.txt")

IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
RESCALE = 1.0 / 255
NUM_CLASSES = 9
CLEAR_SKIN_FOLDER = "CS- clear skin"

# Hamming distance thresholds (out of 256 bits) at which to exclude a test
# image as a duplicate of some training image.
#   0  = perceptually identical. Indisputably leaked.
#   6  = near-identical; catches re-encodes, mild crops and augmentation.
THRESHOLDS = [None, 0, 2, 4, 6]      # None = no exclusion (raw, for comparison)
HEADLINE_THRESHOLD = 0               # the number to quote
HASH_SIDE = 16                       # 16x16 => 256-bit hash

REPORT_PATH = os.path.join(HERE, "evaluation_report.txt")
MATRIX_PATH = os.path.join(HERE, "confusion_matrix.png")
IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def fail(msg):
    sys.exit("ERROR: " + msg)


for d, label in ((TRAIN_DIR, "train_set"), (TEST_DIR, "test_set")):
    if not os.path.isdir(d):
        fail("%s not found at:\n  %s\nEdit DATASET_ROOT at the top of this script." % (label, d))
if not os.path.isfile(WEIGHTS):
    fail("model.weights.h5 not found at:\n  %s" % WEIGHTS)


# ----------------------------------------------------------------------------
# 1. Load the test set
# ----------------------------------------------------------------------------
print("Loading test_set...\n")

test_ds = tf.keras.preprocessing.image_dataset_from_directory(
    TEST_DIR, image_size=IMAGE_SIZE, batch_size=BATCH_SIZE,
    shuffle=False, label_mode="int",
)
discovered = list(test_ds.class_names)
test_paths = list(test_ds.file_paths)      # same order as the batches

print("\nClasses discovered, in label order:")
for i, c in enumerate(discovered):
    print("  [%d] %s" % (i, c))

if len(discovered) != NUM_CLASSES:
    fail("Expected %d class folders, found %d." % (NUM_CLASSES, len(discovered)))

pretty_names = discovered
if os.path.isfile(CLASS_NAMES_FILE):
    with open(CLASS_NAMES_FILE, encoding="utf-8") as f:
        declared = [ln.strip() for ln in f if ln.strip()]
    if len(declared) == NUM_CLASSES:
        pretty_names = declared
        print("\nclass_names.txt (must correspond index-for-index with the above):")
        for i, c in enumerate(declared):
            print("  [%d] %s" % (i, c))

try:
    clear_idx = discovered.index(CLEAR_SKIN_FOLDER)
except ValueError:
    fail("Clear-skin folder %r not found." % CLEAR_SKIN_FOLDER)


# ----------------------------------------------------------------------------
# 2. Leakage detection by perceptual hash
# ----------------------------------------------------------------------------
def list_images(root):
    out = []
    for dp, _, fns in os.walk(root):
        for fn in sorted(fns):
            if fn.lower().endswith(IMG_EXT):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def ahash(path):
    """16x16 average hash: 256 bits, robust to re-encoding and mild resizing."""
    try:
        im = Image.open(path).convert("L").resize((HASH_SIDE, HASH_SIDE), Image.BILINEAR)
    except Exception:
        return None
    a = np.asarray(im, dtype=np.float32)
    return (a > a.mean()).flatten()


print("\n\nChecking train/test leakage by perceptual hash...")

train_paths = list_images(TRAIN_DIR)
train_hashes = []
for p in train_paths:
    h = ahash(p)
    if h is not None:
        train_hashes.append(h)
train_hashes = np.array(train_hashes, dtype=bool)
print("  hashed %d train images" % len(train_hashes))

min_dist = np.zeros(len(test_paths), dtype=int)
nearest = [""] * len(test_paths)
for i, p in enumerate(test_paths):
    h = ahash(p)
    if h is None:
        min_dist[i] = 999
        continue
    d = (train_hashes ^ h).sum(axis=1)
    j = int(d.argmin())
    min_dist[i] = int(d.min())
    nearest[i] = os.path.basename(train_paths[j])
print("  hashed %d test images\n" % len(test_paths))

print("Leakage profile:")
for th in [0, 2, 4, 6, 8, 10]:
    k = int((min_dist <= th).sum())
    print("  min hamming <= %2d : %4d of %d test images  (%.1f%%)"
          % (th, k, len(test_paths), 100.0 * k / len(test_paths)))
print()


# ----------------------------------------------------------------------------
# 3. Rebuild the architecture and load trained weights
# ----------------------------------------------------------------------------
print("Rebuilding model and loading weights...")

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(IMAGE_SIZE[0], IMAGE_SIZE[1], 3), include_top=False, weights=None)
base_model.trainable = False

model = tf.keras.models.Sequential([
    base_model,
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(NUM_CLASSES, activation="softmax"),
])
model.build((None, IMAGE_SIZE[0], IMAGE_SIZE[1], 3))
model.load_weights(WEIGHTS)

print("Running inference...\n")
y_true, y_prob = [], []
for images, labels in test_ds:
    y_prob.append(model.predict(images * RESCALE, verbose=0))
    y_true.append(labels.numpy())
y_true = np.concatenate(y_true)
y_prob = np.concatenate(y_prob)
y_pred = y_prob.argmax(axis=1)
confidence = y_prob.max(axis=1)


# ----------------------------------------------------------------------------
# 4. Metrics at each threshold
# ----------------------------------------------------------------------------
def evaluate(mask):
    yt, yp, cf = y_true[mask], y_pred[mask], confidence[mask]
    n = len(yt)
    if n == 0:
        return None
    counts = np.bincount(yt, minlength=NUM_CLASSES)
    rd = classification_report(yt, yp, labels=list(range(NUM_CLASSES)),
                               target_names=pretty_names, output_dict=True, zero_division=0)
    cond = yt != clear_idx
    n_cond = int(cond.sum())
    missed = int((yp[cond] == clear_idx).sum())
    ok = yp == yt
    return {
        "n": n,
        "accuracy": float(ok.mean()),
        "baseline": float(counts.max() / n),
        "baseline_cls": pretty_names[int(counts.argmax())],
        "macro_f1": rd["macro avg"]["f1-score"],
        "report_txt": classification_report(yt, yp, labels=list(range(NUM_CLASSES)),
                                            target_names=pretty_names, digits=3, zero_division=0),
        "cm": confusion_matrix(yt, yp, labels=list(range(NUM_CLASSES))),
        "n_cond": n_cond,
        "missed": missed,
        "missed_rate": missed / n_cond if n_cond else 0.0,
        "conf_ok": float(cf[ok].mean()) if ok.any() else float("nan"),
        "conf_bad": float(cf[~ok].mean()) if (~ok).any() else float("nan"),
        "per_class": [(pretty_names[i],
                       int(((yt == i) & (yp == clear_idx)).sum()),
                       int((yt == i).sum()))
                      for i in range(NUM_CLASSES) if i != clear_idx and (yt == i).any()],
    }


results = {}
for th in THRESHOLDS:
    mask = np.ones(len(y_true), dtype=bool) if th is None else (min_dist > th)
    results[th] = evaluate(mask)

head = results[HEADLINE_THRESHOLD]
raw = results[None]


# ----------------------------------------------------------------------------
# 5. Report
# ----------------------------------------------------------------------------
L = []
w = L.append

w("=" * 78)
w("DERMAID: HELD-OUT EVALUATION WITH LEAKAGE CONTROL")
w("=" * 78)
w("Generated:  %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
w("Test set:   %s" % TEST_DIR)
w("Train set:  %s" % TRAIN_DIR)
w("Weights:    %s" % WEIGHTS)
w("")
w("-" * 78)
w("LEAKAGE BETWEEN TRAIN AND TEST")
w("-" * 78)
w("Similarity measured by 16x16 average hash (256 bits). Hamming distance 0")
w("means the two images are perceptually identical.")
w("")
w("  threshold      test images excluded      remaining")
for th in [0, 2, 4, 6, 8, 10]:
    k = int((min_dist <= th).sum())
    w("  <= %-2d          %4d  (%5.1f%%)             %4d" %
      (th, k, 100.0 * k / len(test_paths), len(test_paths) - k))
w("")
w("The shipped test_set is therefore NOT a clean held-out split. It shares a")
w("substantial fraction of its images with train_set, byte-identical in some")
w("cases and re-encoded or lightly augmented in many more. This is an artefact")
w("of how the dataset was assembled from public sources and passed through")
w("Roboflow, not of the training code.")
w("")
w("-" * 78)
w("SENSITIVITY: HOW THE HEADLINE MOVES AS LEAKED IMAGES ARE REMOVED")
w("-" * 78)
w("")
w("  %-22s %6s %10s %10s %12s" % ("exclusion", "n", "accuracy", "macro F1", "cond->clear"))
for th in THRESHOLDS:
    r = results[th]
    if r is None:
        continue
    label = "none (raw)" if th is None else "hamming <= %d" % th
    w("  %-22s %6d %9.1f%% %10.3f %11.1f%%" %
      (label, r["n"], r["accuracy"] * 100, r["macro_f1"], r["missed_rate"] * 100))
w("")
w("Read the raw row as the contaminated number and the others as the honest")
w("range. If accuracy barely moves as duplicates are removed, the model is")
w("generalising. If it falls sharply, the raw figure was measuring memorisation.")
w("")
w("=" * 78)
w("HEADLINE  (excluding test images perceptually identical to a train image)")
w("=" * 78)
w("Images evaluated:         %d of %d" % (head["n"], len(test_paths)))
w("Accuracy:                 %.1f%%" % (head["accuracy"] * 100))
w("Majority-class baseline:  %.1f%%   (always predicting '%s')"
  % (head["baseline"] * 100, head["baseline_cls"]))
w("Lift over baseline:       %+.1f percentage points"
  % ((head["accuracy"] - head["baseline"]) * 100))
w("Macro F1:                 %.3f   (all classes weighted equally)" % head["macro_f1"])
w("")
w("For comparison, the same model on the uncleaned test set: %.1f%% accuracy, "
  "macro F1 %.3f." % (raw["accuracy"] * 100, raw["macro_f1"]))
w("")
w("-" * 78)
w("PER-CLASS BREAKDOWN  (leakage-excluded)")
w("-" * 78)
w(head["report_txt"])
w("-" * 78)
w("CLINICALLY ASYMMETRIC ERROR: CONDITION CLASSIFIED AS CLEAR SKIN")
w("-" * 78)
w("Telling someone with a real condition that their skin is clear is the")
w("dangerous failure mode. Every other confusion still sends them to a clinician.")
w("")
w("Images with a genuine condition:  %d" % head["n_cond"])
w("Classified as clear skin:         %d" % head["missed"])
w("Rate:                             %.1f%%" % (head["missed_rate"] * 100))
w("")
rows = sorted([r for r in head["per_class"]], key=lambda r: -(r[1] / r[2] if r[2] else 0))
if rows:
    w("  %-34s %8s %8s %9s" % ("Condition", "AsClear", "Total", "Rate"))
    for name, as_clear, total_i in rows:
        w("  %-34s %8d %8d %8.1f%%" % (name[:34], as_clear, total_i,
                                       100.0 * as_clear / total_i if total_i else 0.0))
w("")
w("-" * 78)
w("CONFIDENCE  (leakage-excluded)")
w("-" * 78)
w("Mean softmax confidence when correct:    %.3f" % head["conf_ok"])
w("Mean softmax confidence when incorrect:  %.3f" % head["conf_bad"])
w("")
if not np.isnan(head["conf_bad"]) and head["conf_bad"] > 0.85:
    w("The model is nearly as confident when wrong as when right, so raw softmax")
    w("output is not a usable certainty signal without calibration.")
else:
    w("Errors carry visibly lower confidence than correct predictions, so a")
    w("confidence threshold could plausibly gate low-certainty predictions.")
w("")
w("-" * 78)
w("CONFUSION MATRIX  (leakage-excluded; rows = true, columns = predicted)")
w("-" * 78)
w("")
w("%-32s" % "" + "".join("%6d" % i for i in range(NUM_CLASSES)))
for i in range(NUM_CLASSES):
    w("%-32s" % ("[%d] %s" % (i, pretty_names[i][:26])) +
      "".join("%6d" % v for v in head["cm"][i]))
w("")
w("=" * 78)
w("SUMMARY FOR A CV OR STATEMENT OF PURPOSE")
w("=" * 78)
w("")
w("  Found that the dataset's shipped test split shared %.0f%% of its images with"
  % (100.0 * (min_dist <= 0).sum() / len(test_paths)))
w("  the training set (perceptually identical), so evaluated on the %d-image" % head["n"])
w("  deduplicated remainder: %.1f%% accuracy against a %.1f%% majority-class"
  % (head["accuracy"] * 100, head["baseline"] * 100))
w("  baseline, macro F1 %.3f, and a %.1f%% rate of genuine conditions being"
  % (head["macro_f1"], head["missed_rate"] * 100))
w("  classified as clear skin.")
w("")

report = "\n".join(L)
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(report)
print(report)

# Leaked-file manifest, for the record
manifest = os.path.join(HERE, "leaked_test_images.txt")
with open(manifest, "w", encoding="utf-8") as f:
    f.write("Test images with a near-duplicate in train_set (16x16 aHash, 256 bits)\n")
    f.write("distance\ttest_image\tnearest_train_image\n")
    for i in np.argsort(min_dist):
        if min_dist[i] <= 6:
            f.write("%d\t%s\t%s\n" % (min_dist[i], os.path.relpath(test_paths[i], TEST_DIR), nearest[i]))

# ----------------------------------------------------------------------------
# 6. Confusion matrix figure
# ----------------------------------------------------------------------------
cm = head["cm"]
fig, ax = plt.subplots(figsize=(9.5, 8))
cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(NUM_CLASSES)); ax.set_yticks(range(NUM_CLASSES))
ax.set_xticklabels([c[:20] for c in pretty_names], rotation=45, ha="right", fontsize=8)
ax.set_yticklabels([c[:20] for c in pretty_names], fontsize=8)
ax.set_xlabel("Predicted"); ax.set_ylabel("True")
ax.set_title("Dermaid: held-out confusion matrix, leakage-excluded (%d images)\n"
             "cell = count, shading = proportion of that true class" % head["n"], fontsize=11)
for i in range(NUM_CLASSES):
    for j in range(NUM_CLASSES):
        if cm[i, j] > 0:
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=8,
                    color="white" if cm_norm[i, j] > 0.5 else "black")
ax.add_patch(plt.Rectangle((clear_idx - 0.5, -0.5), 1, NUM_CLASSES,
                           fill=False, edgecolor="crimson", linewidth=2))
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="proportion of true class")
fig.tight_layout()
fig.savefig(MATRIX_PATH, dpi=150)

print("\nWrote:")
print("  %s" % REPORT_PATH)
print("  %s" % MATRIX_PATH)
print("  %s" % manifest)
