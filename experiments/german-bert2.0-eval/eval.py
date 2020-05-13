# coding=utf-8
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downstream runner for all experiments in specified config files."""

from pathlib import Path
from experiment import run_experiment, load_experiments
from convert_bert_original_tf_checkpoint_to_pytorch import convert_tf_checkpoint_to_pytorch as convert_tf_to_pt_bert
from convert_albert_original_tf_checkpoint_to_pytorch import convert_tf_checkpoint_to_pytorch as convert_tf_to_pt_albert
from convert_electra_original_tf_checkpoint_to_pytorch import convert_tf_checkpoint_to_pytorch as convert_tf_to_pt_electra

import os
from shutil import copyfile
import torch
import regex as re

CONFIG_FILES = {
    "germEval18Fine": Path("germEval18Fine_config.json"),
    "germEval18Coarse": Path("germEval18Coarse_config.json"),
    "germEval14": Path("germEval14_config.json")
}

model_type = "electra"
bert_config_file = Path("../../saved_models/electra-base-german-dbmdz-fixed-cased/config.json")
checkpoints_folder = Path("../../saved_models/electra-base-german-dbmdz-fixed-cased")
vocab_file = Path("../../saved_models/electra-base-german-dbmdz-fixed-cased/vocab.txt")
tokenizer_model = None
# models = ["xlm-roberta-large"]
mlflow_url = "https://public-mlflow.deepset.ai/"
# mlflow_url = ""
mlflow_experiment = 'Electra'


def convert_checkpoints(dir, model_type):
    if model_type == "bert":
        convert_tf_to_pt = convert_tf_to_pt_bert
    elif model_type == "albert":
        convert_tf_to_pt = convert_tf_to_pt_albert
    elif model_type == "electra":
        convert_tf_to_pt = convert_tf_to_pt_electra

    tf_checkpoints_names = fetch_tf_checkpoints(dir)
    tf_checkpoints = [dir / tfcn for tfcn in tf_checkpoints_names]
    hf_checkpoints = []
    for tfc in tf_checkpoints:
        print(tfc)
        step = re.search("-(\d+)$", str(tfc))[1]
        dump_dir_name = f"pt_{model_type}_" + step
        dump_dir = checkpoints_folder / dump_dir_name
        if not os.path.isdir(dump_dir):
            os.mkdir(dump_dir)
        hf_checkpoints.append(dump_dir)
        convert_tf_to_pt(tfc, bert_config_file, dump_dir / "pytorch_model.bin")
        copyfile(bert_config_file, dump_dir / "config.json")
        copyfile(vocab_file, dump_dir / "vocab.txt")
        if tokenizer_model:
            copyfile(tokenizer_model, dump_dir/"spiece.model")

def fetch_tf_checkpoints(dir):
    files = os.listdir(dir)
    files = [f for f in files if "model.ckpt-" in f]
    checkpoints = set(".".join(f.split(".")[:2]) for f in files)
    checkpoints = sorted(checkpoints, key=lambda x: int(x.split("-")[1]), reverse=True)
    return checkpoints

def fetch_pt_checkpoints(dir):
    files = os.listdir(dir)
    files = [dir / f for f in files if "pt_" in f]
    checkpoints = sorted(files, key=lambda x: int(str(x).replace(f"pt_{model_type}_", "").split("/")[-1].split("-")[0]), reverse=True)
    return checkpoints

def main_from_saved():
    # NOTE: This only needs to be run once
    convert_checkpoints(checkpoints_folder, model_type)

    # checkpoints = fetch_pt_checkpoints(checkpoints_folder)
    # print(f"Performing evaluation on these checkpoints: {checkpoints}")
    # print(f"Performing evaluation using these experiments: {CONFIG_FILES}")
    # for checkpoint in checkpoints:
    #     for i, (conf_name, conf_file) in enumerate(CONFIG_FILES.items()):
    #         experiments = load_experiments(conf_file)
    #         steps = str(checkpoint).split("_")[-1]
    #         for j, experiment in enumerate(experiments):
    #             mlflow_run_name = f"{conf_name}_step{steps}_{j}"
    #             experiment.logging.mlflow_url = mlflow_url
    #             experiment.logging.mlflow_experiment = mlflow_experiment
    #             experiment.logging.mlflow_run_name = mlflow_run_name
    #             experiment.parameter.model = checkpoint
    #             experiment.general.output_dir = str(checkpoint).split("/")[:-1]
    #             run_experiment(experiment)
    #             torch.cuda.empty_cache()

def main_from_downloaded():
    print(f"Performing evaluation on these models: {models}")
    print(f"Performing evaluation using these experiments: {CONFIG_FILES}")
    for model in models:
        for i, (conf_name, conf_file) in enumerate(CONFIG_FILES.items()):
            experiments = load_experiments(conf_file)
            for j, experiment in enumerate(experiments):
                mlflow_run_name = f"{conf_name}_{model}_{j}"
                experiment.logging.mlflow_url = mlflow_url
                experiment.logging.mlflow_experiment = mlflow_experiment
                experiment.logging.mlflow_run_name = mlflow_run_name
                experiment.parameter.model = model
                experiment.general.output_dir = "benchmarks"
                run_experiment(experiment)
                torch.cuda.empty_cache()


if __name__ == "__main__":
    main_from_saved()
    # main_from_downloaded()
