# src/module1_text_emotion.py
# ─────────────────────────────────────────────────────────────
# Module 1 — Text Emotion Detection
# Trains DistilBERT on GoEmotions dataset
# Run: python src/module1_text_emotion.py
# ─────────────────────────────────────────────────────────────

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from datasets import load_dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
)
from torch.utils.data import Dataset
from sklearn.metrics import classification_report, confusion_matrix
from src.config import *

print('=' * 55)
print('  MODULE 1 — Text Emotion Detection')
print('=' * 55)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'  Device : {DEVICE}\n')

# ── GoEmotions → 6 mood mapping ───────────────────────────────
GO_TO_MOOD = {
    'admiration':'positive','amusement':'positive','approval':'positive',
    'caring':'positive','desire':'positive','excitement':'energetic',
    'gratitude':'positive','joy':'positive','love':'positive',
    'optimism':'positive','pride':'positive','relief':'positive',
    'anger':'negative','annoyance':'negative','disappointment':'negative',
    'disapproval':'negative','disgust':'negative','embarrassment':'negative',
    'fear':'stressed','grief':'negative','remorse':'negative','sadness':'negative',
    'nervousness':'stressed','confusion':'neutral','curiosity':'focused',
    'neutral':'neutral','realization':'focused','surprise':'energetic',
}
LABEL2ID = {m: i for i, m in enumerate(MOOD_LABELS)}
ID2LABEL  = {i: m for m, i in LABEL2ID.items()}


# ── Step 1: Load dataset ───────────────────────────────────────
print('Step 1/6 — Loading GoEmotions dataset...')
dataset = load_dataset('go_emotions', 'simplified')

def map_labels(example):
    emotions  = dataset['train'].features['labels'].feature.names
    mapped    = set()
    for idx in example['labels']:
        em   = emotions[idx]
        mood = GO_TO_MOOD.get(em)
        if mood:
            mapped.add(mood)
    if not mapped:
        mapped = {'neutral'}
    example['mood'] = LABEL2ID[list(mapped)[0]]
    return example

dataset = dataset.map(map_labels)
print(f'  Train : {len(dataset["train"])} samples')
print(f'  Val   : {len(dataset["validation"])} samples')
print(f'  Test  : {len(dataset["test"])} samples')


# ── Step 2: EDA ────────────────────────────────────────────────
print('\nStep 2/6 — EDA...')
train_df = pd.DataFrame({'mood': [ID2LABEL[x] for x in dataset['train']['mood']]})
counts   = train_df['mood'].value_counts()

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
counts.plot(kind='bar', ax=axes[0], color=[MOOD_COLORS[m] for m in counts.index], edgecolor='white')
axes[0].set_title('Mood Distribution (Training)', fontweight='bold')
axes[0].set_xlabel('Mood'); axes[0].set_ylabel('Count')
axes[0].tick_params(axis='x', rotation=30)
axes[0].grid(axis='y', alpha=0.3)

axes[1].pie(counts.values, labels=counts.index,
            colors=[MOOD_COLORS[m] for m in counts.index],
            autopct='%1.1f%%', startangle=90)
axes[1].set_title('Mood Distribution %', fontweight='bold')

plt.tight_layout()
chart_path = os.path.join(CHARTS_DIR, '01_text_eda.png')
plt.savefig(chart_path, dpi=150, bbox_inches='tight')
plt.close()
print(f'  Chart saved: {chart_path}')


# ── Step 3: Tokenize ───────────────────────────────────────────
print('\nStep 3/6 — Tokenizing...')
tokenizer = DistilBertTokenizerFast.from_pretrained(TEXT_BASE_MODEL)

def tokenize(batch):
    return tokenizer(batch['text'], truncation=True,
                     padding='max_length', max_length=MAX_SEQ_LEN)

tokenized = dataset.map(tokenize, batched=True)
tokenized.set_format('torch', columns=['input_ids','attention_mask','mood'])


# ── Step 4: Model ─────────────────────────────────────────────
print('\nStep 4/6 — Setting up model...')

class MoodDataset(Dataset):
    def __init__(self, hf_dataset):
        self.data = hf_dataset
    def __len__(self):
        return len(self.data)
    def __getitem__(self, idx):
        item = self.data[idx]
        return {
            'input_ids'     : item['input_ids'],
            'attention_mask': item['attention_mask'],
            'labels'        : item['mood'],
        }

train_ds = MoodDataset(tokenized['train'])
val_ds   = MoodDataset(tokenized['validation'])
test_ds  = MoodDataset(tokenized['test'])

# Class weights for imbalanced data
label_counts = np.array([sum(1 for x in dataset['train']['mood'] if x == i)
                          for i in range(len(MOOD_LABELS))])
class_weights = torch.tensor(1.0 / (label_counts + 1e-6), dtype=torch.float).to(DEVICE)

model = DistilBertForSequenceClassification.from_pretrained(
    TEXT_BASE_MODEL,
    num_labels=len(MOOD_LABELS),
    id2label=ID2LABEL,
    label2id=LABEL2ID,
).to(DEVICE)


# ── Step 5: Train ─────────────────────────────────────────────
print('\nStep 5/6 — Training...')

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc   = (preds == labels).mean()
    return {'accuracy': acc}

args = TrainingArguments(
    output_dir                  = TEXT_MODEL_PATH,
    num_train_epochs            = TRAIN_EPOCHS,
    per_device_train_batch_size = TRAIN_BATCH,
    per_device_eval_batch_size  = TRAIN_BATCH,
    learning_rate               = LEARNING_RATE,
    evaluation_strategy         = 'epoch',
    save_strategy               = 'epoch',
    load_best_model_at_end      = True,
    metric_for_best_model       = 'accuracy',
    logging_steps               = 100,
    warmup_ratio                = 0.1,
    weight_decay                = 0.01,
    report_to                   = 'none',
    gradient_accumulation_steps = 4,    
    fp16                        = True, 
)

trainer = Trainer(
    model           = model,
    args            = args,
    train_dataset   = train_ds,
    eval_dataset    = val_ds,
    compute_metrics = compute_metrics,
)

trainer.train()

# Save model
model.save_pretrained(TEXT_MODEL_PATH)
tokenizer.save_pretrained(TEXT_MODEL_PATH)
print(f'  Model saved: {TEXT_MODEL_PATH}')


# ── Step 6: Evaluate ──────────────────────────────────────────
print('\nStep 6/6 — Evaluating...')
preds_out = trainer.predict(test_ds)
preds     = np.argmax(preds_out.predictions, axis=-1)
labels    = preds_out.label_ids

report = classification_report(labels, preds,
                                target_names=MOOD_LABELS, digits=3)
print(report)

# Log
log_df = pd.DataFrame([{
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'module': 'text_emotion',
    'accuracy': float((preds == labels).mean()),
}])
log_df.to_csv(os.path.join(LOGS_DIR, 'text_training_log.csv'), index=False)

# Confusion matrix
cm  = confusion_matrix(labels, preds)
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', ax=ax,
            xticklabels=MOOD_LABELS, yticklabels=MOOD_LABELS,
            cmap='Blues')
ax.set_title('Text Model — Confusion Matrix', fontweight='bold')
ax.set_xlabel('Predicted'); ax.set_ylabel('True')
plt.tight_layout()
chart_path = os.path.join(CHARTS_DIR, '02_text_model_eval.png')
plt.savefig(chart_path, dpi=150, bbox_inches='tight')
plt.close()
print(f'  Chart saved: {chart_path}')
print('\n✅ Module 1 complete!')


# ── Quick test ─────────────────────────────────────────────────
if __name__ == '__main__':
    print('\n--- Quick Test ---')
    from transformers import pipeline
    clf = pipeline('text-classification', model=TEXT_MODEL_PATH,
                   tokenizer=TEXT_MODEL_PATH, top_k=None)
    tests = [
        'I feel amazing and ready to take on anything!',
        'I am so stressed and overwhelmed with work.',
        'Just another normal day at the office.',
    ]
    for t in tests:
        result   = clf(t)
        if isinstance(result[0], list): result = result[0]
        scores   = {r['label']: r['score'] for r in result}
        dominant = max(scores, key=scores.get)
        print(f'  "{t[:45]}..."')
        print(f'  → {dominant.upper()} {MOOD_EMOJI[dominant]} ({scores[dominant]*100:.1f}%)\n')
