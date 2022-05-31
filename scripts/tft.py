import sys

sys.path.append("../../pytorch-forecasting")
sys.path.append("../")

import pytorch_lightning as pl
import seaborn as sns
import torch
from data_factory.dataLoader import StockPricesLoader
from pytorch_lightning.callbacks import EarlyStopping, LearningRateMonitor
from pytorch_lightning.loggers import TensorBoardLogger
from tqdm import notebook

from pytorch_forecasting import Baseline
from utilities import *

pl.seed_everything(42)

config = load_config("../config/config.yml")

assert config['model'] == 'temporal_fusion_transformer', 'Invalid model in file configuration for this script'

dl = StockPricesLoader(use_previous_files=True)
if not dl.initialized:
    dl.init()


from pytorch_forecasting.models import TemporalFusionTransformer
import logging
from logging import WARNING
logging.basicConfig(level=WARNING)

early_stop_callback = EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=10, verbose=False, mode="min")
lr_logger = LearningRateMonitor()  # log the learning rate
logger = TensorBoardLogger("lightning_logs")  # logging results to a tensorboard


args = dict(
    hidden_size=16, #config['temporal_fusion_transformer']['hidden_size'],
    lstm_layers=1, #config['temporal_fusion_transformer']['lstm_layers'],
    dropout=config['temporal_fusion_transformer']['dropout'],
    attention_head_size=4,#config['temporal_fusion_transformer']['attention_head_size']
    # output_size=dl.max_prediction_length,
    # max_encoder_length=dl.max_encoder_length
)

# configure network and trainer
trainer = pl.Trainer(
    accelerator='gpu',
    gradient_clip_val=0.1,
    # clipping gradients is a hyperparameter and important to prevent divergence
    # of the gradient for recurrent neural networks
    auto_lr_find=True,
    callbacks=[lr_logger, early_stop_callback],
    logger=logger,
    weights_summary="top",
)

model = TemporalFusionTransformer.from_dataset(
    dl.df_train_timeseries,
    **args
)


print(f"Number of parameters in network: {model.size() / 1e3:.1f}k")


## fit network

fit = True

if fit:
    trainer.fit(model, train_dataloaders=dl.train_dl, val_dataloaders=dl.val_dl)
else:
    model = TemporalFusionTransformer.load_from_checkpoint('././lightning_logs/lightning_logs/version_5/checkpoints/epoch=0-step=49915.ckpt')
