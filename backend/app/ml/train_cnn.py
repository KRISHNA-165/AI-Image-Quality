"""
CNN Training Script.

Generates synthetic degraded image thumbnails (64x64 RGB), trains the DefectCNN
model using standard PyTorch training loop, evaluates on held-out test set, and
saves the trained weights + metrics.

Uses the same hardened apply_degradation() from train.py to ensure consistency
between the RF and CNN training data distributions.
"""

import os
import sys
import json
import random
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from backend.app.ml.cnn_model import DefectCNN
from backend.app.ml.train import generate_base_synthetic_image, apply_degradation

CLASSES = DefectCNN.CLASSES  # Alphabetical: ACCEPTABLE, BLUR, DEFECTIVE, NOISE, OVEREXPOSURE, UNDEREXPOSURE
IMG_SIZE = DefectCNN.INPUT_SIZE  # 64


def prepare_thumbnail(img_bgr: np.ndarray) -> np.ndarray:
    """Resize BGR image to 64x64 and convert to CHW float32 tensor-ready array."""
    thumb = cv2.resize(img_bgr, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    # BGR -> RGB, HWC -> CHW, normalize to [0, 1]
    rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
    chw = np.transpose(rgb, (2, 0, 1)).astype(np.float32) / 255.0
    return chw


def generate_cnn_dataset(samples_per_class: int = 250):
    """Generate thumbnail arrays and labels for CNN training."""
    X_imgs = []
    y_labels = []

    # Map from train.py class names to CNN alphabetical order
    train_classes = ["ACCEPTABLE", "BLUR", "UNDEREXPOSURE", "OVEREXPOSURE", "NOISE", "DEFECTIVE"]

    for cls in train_classes:
        cnn_label = CLASSES.index(cls)
        print(f"  -> CNN class {cls} (label={cnn_label}): {samples_per_class} images")
        for _ in range(samples_per_class):
            base = generate_base_synthetic_image(random.choice([128, 192, 256]))
            degraded, _ = apply_degradation(base, cls)
            thumb = prepare_thumbnail(degraded)
            X_imgs.append(thumb)
            y_labels.append(cnn_label)

    return np.array(X_imgs), np.array(y_labels)


def run_cnn_training():
    """Full CNN training pipeline."""
    print("=" * 60)
    print("CNN TRAINING PIPELINE (DefectCNN)")
    print("=" * 60)

    device = torch.device("cpu")
    model = DefectCNN(num_classes=len(CLASSES)).to(device)
    print(f"Model parameters: {model.parameter_count():,}")
    print(f"Classes: {CLASSES}")

    # Generate dataset
    print("\nGenerating CNN training thumbnails...")
    X_all, y_all = generate_cnn_dataset(samples_per_class=250)
    print(f"Total dataset: {len(X_all)} images")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.20, random_state=42, stratify=y_all
    )
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Create DataLoaders
    train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train).long())
    test_ds = TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_test).long())
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

    # Training
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=8, gamma=0.5)

    num_epochs = 20
    print(f"\nTraining for {num_epochs} epochs on {device}...")

    for epoch in range(1, num_epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * batch_x.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == batch_y).sum().item()
            total += batch_y.size(0)

        scheduler.step()
        epoch_loss = running_loss / total
        epoch_acc = correct / total

        if epoch % 5 == 0 or epoch == 1:
            print(f"  Epoch {epoch:2d}/{num_epochs}: loss={epoch_loss:.4f}, train_acc={epoch_acc:.4f}")

    # Evaluation on test set
    print("\nEvaluating on held-out test set...")
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            outputs = model(batch_x.to(device))
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch_y.numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    acc = float(accuracy_score(all_labels, all_preds))
    f1 = float(f1_score(all_labels, all_preds, average="macro"))

    print("\n" + "=" * 50)
    print("CNN EVALUATION RESULTS")
    print("=" * 50)
    print(f"Test Accuracy:   {acc * 100:.2f}%")
    print(f"Macro F1-Score:  {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(all_labels, all_preds, target_names=CLASSES))

    conf_mat = confusion_matrix(all_labels, all_preds).tolist()

    # Save model weights
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models_store"))
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, "cnn_model.pt")
    torch.save(model.state_dict(), model_path)
    print(f"\nCNN weights saved to {model_path}")

    # Save CNN metrics
    cnn_metrics = {
        "accuracy": round(acc, 4),
        "f1_macro": round(f1, 4),
        "classes": CLASSES,
        "confusion_matrix": conf_mat,
        "num_parameters": model.parameter_count(),
        "num_epochs": num_epochs,
        "test_sample_count": len(X_test),
        "total_sample_count": len(X_all),
    }

    with open(os.path.join(models_dir, "cnn_metrics.json"), "w") as f:
        json.dump(cnn_metrics, f, indent=2)

    print(f"CNN metrics saved to {os.path.join(models_dir, 'cnn_metrics.json')}")
    print("CNN pipeline complete.\n")


if __name__ == "__main__":
    run_cnn_training()
