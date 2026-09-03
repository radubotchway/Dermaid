# Running the held-out evaluation, and what to do with the result

Companion to `evaluate_heldout.py`. Written 3 Sep 2026.

## Why this matters

`train_model.py` only ever pointed at `train_set` and took `validation_split=0.2` from it. So the 95.2% in the README is a **model-selection split**, not an estimate of how the model generalises. Meanwhile a real `test_set` of 326 images across all nine classes shipped with the dataset and was never touched.

`test_model.py` claims in the README to evaluate on a held-out set. It does not. It loads the weights and predicts on one hardcoded image path. It is a manual inference demo.

This is roughly an afternoon of work and it is the single cheapest upgrade available to your graduate applications. A real held-out 80% with a per-class breakdown reads as far more competent to an admissions committee than an unqualified 95%.

---

## Step 1: Install the one missing dependency

Your Dermaid venv has TensorFlow 2.16.1, Keras 3.4.1, numpy, matplotlib and Pillow. It does not have scikit-learn.

```
cd C:\Users\ronar\Desktop\Programming\Dermaid
venv\Scripts\activate
pip install scikit-learn
```

## Step 2: Run it

```
cd model
python evaluate_heldout.py
```

Takes a couple of minutes on CPU. It writes two files into the `model` folder:

- `evaluation_report.txt`
- `confusion_matrix.png`

## Step 3: Check the class ordering before trusting anything

The script prints two lists at the top: the folder order Keras discovered, and what `class_names.txt` declares. **Read them side by side.**

They should correspond index for index:

| Index | Folder | class_names.txt |
|---|---|---|
| 0 | `BA- cellulitis` | Cellulitis |
| 1 | `BA-impetigo` | Impetigo |
| 2 | `CS- clear skin` | Clear Skin |
| 3 | `FU-athlete-foot` | Athlete-Foot |
| 4 | `FU-nail-fungus` | Nail Fungus |
| 5 | `FU-ringworm` | Ringworm |
| 6 | `PA-cutaneous-larva-migrans` | Cutaneous Larva Migrans |
| 7 | `VI-chickenpox` | Chicken Pox |
| 8 | `VI-shingles` | Shingles |

This works only because the clear-skin folder carries a `CS-` prefix that sorts it into third place. Nothing in the codebase enforces the agreement. If you ever rename a folder or drop the prefixes, every prediction gets silently mislabelled with no error raised. That is worth fixing properly later by writing class names out from `train_dataset.class_names` at training time.

---

## Step 4: Read the numbers

The report leads with four figures. Here is how to read each one.

**Held-out accuracy.** The honest number. Expect it to be below 95%. That gap is not a failure, it is the finding.

**Majority-class baseline.** The test set is 92/326 clear skin, so always guessing "clear skin" scores **28.2%**. Any accuracy claim has to be read against that floor. (Note the training set is far more skewed, at 47% clear skin, which is why the model may be biased toward that class even though the test set is less imbalanced.)

**Macro F1.** Weights all nine classes equally regardless of size. This is the number to lead with in an academic context, because it does not let a model hide behind the majority class.

**Condition classified as clear skin.** The clinically asymmetric error. Every other confusion still sends someone to a clinician; this one tells a person with a real condition that they are fine. The report breaks it down per condition, worst first, and the red box on the confusion matrix marks the same thing visually.

### What different outcomes mean

| Result | Reading | What to do |
|---|---|---|
| 70 to 85% accuracy | A normal, defensible held-out result | Report it directly, with macro F1 |
| 50 to 70% | Real generalisation gap, still well above baseline | Report it, and name the gap as the finding |
| Near 28% | The model is barely beating majority prediction | Still report it. This is a genuine and interesting negative result |
| Above 90% | Possible, but check the ordering in step 3 first | Verify before believing it |

**Do not bin a bad number.** A candidate who ran the right evaluation and reports a disappointing result honestly is a better research prospect than one who reports a flattering number from the wrong split. The evaluation itself is the credential here, not the score.

The confidence section tells you something extra: if the model is as confident when wrong as when right, softmax output is not usable as a certainty signal, which is a concrete argument against surfacing a raw confidence score in the UI without calibration.

---

## Step 5: Update the documents

The report ends with a ready-made summary sentence. Use it.

**Academic CV** (`Job Documents\Applications\Master Resume\Ronard_Adu-Botchway_Academic_CV.docx`). Replace the third Dermaid bullet, the one currently beginning "Reported 95.2% accuracy on a validation split", with the real result. Keep the reasoning about why accuracy was the wrong metric; just change it from a thing you identified to a thing you measured. That is a significant upgrade to the strongest section of the document.

**Industry master resume.** No accuracy figure appears there deliberately, so nothing needs changing unless you want to add the macro F1.

**README** (`Dermaid\README.md`). Two corrections, both real defects:

1. It says 762 images, roughly 85 per class. The training directory holds 1,751, severely imbalanced, with clear skin at 47%.
2. It says `test_model.py` evaluates on the held-out test set. It does not. Either rewrite that line to describe what the script does (single-image inference demo) or point it at `evaluate_heldout.py` now that a real evaluation exists.

Keep your existing paragraph reading the training curves verbatim. It is the most credible writing in your public portfolio.

**Hugging Face Space.** The disclaimer currently says "trained on 762 images". Correct it to 1,751 and consider adding the held-out per-class result. Edit `index.html` in `huggingface\dermaid-space-static`, then:

```
cd C:\Users\ronar\Desktop\Programming\huggingface\dermaid-space-static
hf upload Radubotchway/dermaid-demo index.html index.html --repo-type=space
```

## Step 6: Commit

```
cd C:\Users\ronar\Desktop\Programming\Dermaid
git add model/evaluate_heldout.py model/evaluation_report.txt model/confusion_matrix.png README.md
git commit -m "Add held-out evaluation on the untouched test set"
git push
```

Committing the report and the matrix matters: it means anyone reading the repo sees that a real evaluation exists, rather than having to take your word for it.

---

## If something goes wrong

**`scikit-learn is not installed`** — the venv is not active. Run `venv\Scripts\activate` first; the prompt should show `(venv)`.

**`test_set not found`** — edit `TEST_DIR` at the top of the script. It currently points at:
`C:\Users\ronar\Desktop\Programming\AI-Based Skin Disease Diagnosis Tool\Dataset\archive\skin-disease-datasaet\test_set`

**Weight loading errors.** The script rebuilds the architecture to match `train_model.py` exactly: MobileNetV2 at 128x128x3 with `include_top=False`, frozen, then GlobalAveragePooling2D, Dense(128, relu), Dense(9, softmax). If Keras complains about mismatched shapes, the architecture has drifted from what produced the weights. Do not "fix" it by changing layer sizes until the error goes away, since that silently produces a wrong evaluation. Check `train_model.py` instead.

**Everything predicts one class.** Usually means preprocessing does not match training. The script rescales by 1/255, matching the `Rescaling(1./255)` layer applied to the datasets in `train_model.py`. If you ever retrain with different preprocessing, update `RESCALE` here to match.

---

## Worth doing next, if you have the time

The Skin-Tone GAN's `results` and `samples` directories are empty, so the trained outputs were never retained. Re-running it long enough to produce even a small set of sample translations would give you a figure to show, and the pairing of "here is the bias I identified, here is the augmentation I built, here is what it did to per-class recall on darker skin" would be a genuinely strong research narrative rather than two separate projects.

That is a larger job than this one. But it is the thing that would most distinguish the application.
