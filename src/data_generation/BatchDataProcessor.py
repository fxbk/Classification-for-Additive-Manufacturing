from tqdm import tqdm
import numpy as np
from src.data_generation.MeshModel import MeshModel


class BatchDataProcessor:
    """
    Data generator class which yields data batches to the caller.
    """

    def __init__(self, filepaths: list, batch_size: int, transformer: object, target_path: str):
        self.filepaths = filepaths
        self.file = None
        self.batch_size = batch_size
        self.pointer = 0
        self.transformer = transformer
        self.target_path = target_path

    def _load_data_batch(self):
        for _ in tqdm(range(int(np.floor(len(self.filepaths) / self.batch_size))), desc="[INFO]: Processing batch"):
            data_batch = []
            for self.file in tqdm(self.filepaths[self.pointer:(self.pointer + self.batch_size)],
                                  desc=f"[INFO]: Loading data batches of size {self.batch_size}!"):
                data_batch.append(MeshModel(self.file))
            self.pointer += self.batch_size

            yield data_batch

        data_batch = []
        if self.pointer != len(self.filepaths):
            for self.file in tqdm(self.filepaths[self.pointer:len(self.filepaths)],
                                  desc=f"[INFO]: Loading data batches of size {len(self.filepaths) - self.pointer}!"):
                data_batch.append(MeshModel(self.file))

            yield data_batch

    def _save_model(self, models):
        if type(models) is list:
            for model_instance in models:
                model_instance.save(self.target_path)
        else:
            models.save(self.target_path)

    def process(self):
        for batch in self._load_data_batch():
            for model in tqdm(batch, desc="[INFO]: Running models through the pipeline"):
                if self.transformer is not None:
                    models = self.transformer(model)
                self._save_model(models)
