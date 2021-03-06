import numpy as np
import mlflow
import torch
import sys
import os
import logging
from tqdm import tqdm
import horovod.torch as hvd
from sklearn.metrics import confusion_matrix, roc_curve, auc, f1_score, accuracy_score


class PerformanceAnalyst:
    """# TODO: Docstring"""

    def __init__(self, config: object, val_data: object, nn_model: object, trainer: object, val_dataloader: object):
        """# TODO: Docstring"""
        self.config = config
        self.val_data = val_data
        self.nn_model = nn_model.nn_model
        self.trainer = trainer
        self.val_dataloader = val_dataloader

    def start_performance_analysis(self):
        """# TODO: Docstring"""

        with torch.no_grad():

            logging.info('Start performance analysis')

            self.nn_model = self.nn_model.cpu()
            self.nn_model.eval()

            # predictions = self.trainer.predict(self.nn_model, self.val_dataloader)
            #
            # print("#######################################")
            # print("Start new prediction")
            # print(predictions)
            # print("End new prediction")
            # print("#######################################")

            # Get true labels & predicted labels
            true_labels = []
            val_models = []
            pred_labels = []
            prob_labels = []
            for i in tqdm(range(len(self.val_data)), desc="Performing performance analysis"):
                true_labels.append(self.val_data[i][1])
                # val_models.append(self.val_data[i][0])

                score = self.nn_model(torch.unsqueeze(self.val_data[i][0], 0))
                prob_labels.append(score)
                pred_labels.append(torch.round(score))
                # pred_labels.append(torch.round(self.nn_model(torch.unsqueeze(self.val_data[i][0], 0))))

            # Compute accuracy score and store result using MLflow
            if hvd.rank() == 0:
                mlflow.log_param("val_accuracy_score", accuracy_score(np.array(true_labels, dtype=int),
                                                                    torch.Tensor(pred_labels).numpy()))

            # Compute F1 score and store result using MLflow
            if hvd.rank() == 0:
                mlflow.log_param("val_f1_score", f1_score(np.array(true_labels, dtype=int),
                                                        torch.Tensor(pred_labels).numpy()))

            # Compute confusion matrix and store results using MLflow
            tn, fp, fn, tp = confusion_matrix(np.array(true_labels, dtype=int),
                                              torch.Tensor(pred_labels).numpy()).ravel()
            if hvd.rank() == 0:                                              
                mlflow.log_param("confusion_mat_true_negative", tn)
                mlflow.log_param("confusion_mat_false_positive", fp)
                mlflow.log_param("confusion_mat_false_negative", fn)
                mlflow.log_param("confusion_mat_true_positive", tp)

            # Compute ROC/AUC and store results using MLflow
            fpr, tpr, _ = roc_curve(np.array(true_labels, dtype=int), torch.Tensor(prob_labels).numpy())
            roc_auc = auc(fpr, tpr)
            if hvd.rank() == 0:
                mlflow.log_param("roc_false_positive_rate", str(fpr))
                mlflow.log_param("roc_true_positive_rate", str(tpr))
                mlflow.log_param("roc_area_under_curve", roc_auc)

            # models = torch.stack(val_models, dim=0)

            # Compare true labels and predicted labels
            # result = np.equal(np.array(true_labels, dtype=int), pred_labels.detach().numpy().flatten())
            result = np.equal(np.array(true_labels, dtype=int), torch.Tensor(pred_labels).numpy())

            # Get indices of failed predictions and store respective model path
            failure_idx = list(np.where(result == False)[0])
            failed_models = []
            for i in failure_idx:
                failed_models.append(self.val_data.dataset.models[i])

            if hvd.rank() == 0:
                # Store paths/names of failed models using MLflow
                orig_stdout = sys.stdout
                f = open('failed_models.txt', 'w')
                sys.stdout = f
                for i in range(len(failed_models)):
                    print(failed_models[i])
                sys.stdout = orig_stdout
                f.close()
                mlflow.log_artifact("failed_models.txt", artifact_path="failed_models")
                os.remove("failed_models.txt")
