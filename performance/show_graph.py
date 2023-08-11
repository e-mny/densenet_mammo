import matplotlib.pyplot as plt
import datetime
from sklearn.metrics import roc_curve, auc, precision_recall_curve


def plotGraph(train_loss_history, train_accuracy_history, val_loss_history, val_accuracy_history, num_epochs, y_test, y_prob):
    print("Plotting graph now")

    # AUC & PRAUC
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)

    ## Calculate precision-recall values
    precision, recall, _ = precision_recall_curve(y_test, y_prob)

    ## Calculate PR AUC score
    pr_auc = auc(recall, precision)

    # Accuracy and Losses

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot ROC AUC curve and PR AUC curve
    ax1.plot(fpr, tpr, color='darkorange', lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
    ax1.plot(recall, precision, color='blue', lw=2, label='PR AUC (area = %0.2f)' % pr_auc)
    ax1.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    ax1.set_xlim([0.0, 1.0])
    ax1.set_ylim([0.0, 1.05])
    ax1.set_xlabel('False Positive Rate / Recall')
    ax1.set_ylabel('True Positive Rate / Precision')
    ax1.set_title('ROC and PR AUC Curves')
    ax1.legend(loc="lower right")

    # Plot accuracy and loss
    ax2.subplot(1, 2, 1)
    ax2.plot(range(1, num_epochs+1), train_loss_history, label='Train Loss')
    ax2.plot(range(1, num_epochs+1), val_loss_history, label='Validation Loss')
    ax2.xlabel('Epochs')
    ax2.ylabel('Loss')
    ax2.title('Training and Validation Loss')
    ax2.legend()

    ax2.subplot(1, 2, 2)
    ax2.plot(range(1, num_epochs+1), train_accuracy_history, label='Train Accuracy')
    ax2.plot(range(1, num_epochs+1), val_accuracy_history, label='Validation Accuracy')
    ax2.xlabel('Epochs')
    ax2.ylabel('Accuracy')
    ax2.title('Training and Validation Accuracy')
    ax2.legend()

    plt.tight_layout()
    plt.show()
    timenow = datetime.datetime.now()
    formatted_datetime = timenow.strftime("%d-%m-%Y_%H%M%S")
    plt.savefig(f"./results/{formatted_datetime}.png")