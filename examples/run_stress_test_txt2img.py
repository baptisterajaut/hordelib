# This tests running hordelib standalone, as an external caller would use it.
# Call with: python -m test.run_stress_test_txt2img
# You need all the deps in whatever environment you are running this.
import os
import time

if __name__ != "__main__":
    exit(0)
import random

random.seed(999)

import hordelib

hordelib.initialise(setup_logging=False)

import threading

from loguru import logger

from hordelib.horde import HordeLib
from hordelib.shared_model_manager import SharedModelManager

os.makedirs("images/stresstest/", exist_ok=True)

generate = HordeLib()
SharedModelManager.loadModelManagers(compvis=True, controlnet=True)
SharedModelManager.manager.load("Deliberate")
SharedModelManager.manager.load("Anything Diffusion")
SharedModelManager.manager.load("Realistic Vision")
SharedModelManager.manager.load("URPM")

models = ["Deliberate", "Anything Diffusion", "Realistic Vision", "URPM"]
SAMPLERS_MAP = {
    "k_euler": "euler",
    "k_euler_a": "euler_ancestral",
    "k_heun": "heun",
    "k_dpm_2": "dpm_2",
    "k_dpm_2_a": "dpm_2_ancestral",
    "k_lms": "lms",
    "k_dpm_fast": "dpm_fast",
    "k_dpm_adaptive": "dpm_adaptive",
    "k_dpmpp_2s_a": "dpmpp_2s_ancestral",
    "k_dpmpp_sde": "dpmpp_sde",
    "k_dpmpp_2m": "dpmpp_2m",
    "ddim": "ddim",
    "uni_pc": "uni_pc",
    "uni_pc_bh2": "uni_pc_bh2",
    "plms": "euler",
}

start_time = time.time()

ITERATIONS = 50

mutex = threading.Lock()
count = 0


def inc():
    with mutex:
        global count
        count += 1
        return count


def generate_images():
    i = inc()
    logger.info(f"Thread {threading.current_thread().ident} starting iteration {i}")
    model = random.choice(models)
    sampler = random.choice(list(SAMPLERS_MAP.keys()))
    data = {
        "sampler_name": sampler,
        "cfg_scale": 7.5,
        "denoising_strength": 1.0,
        "seed": 123456789,  # random.randint(1, 1000000000),
        "height": 512,
        "width": 512,
        "karras": True,
        "tiling": False,
        "hires_fix": False,
        "clip_skip": 1,
        "control_type": None,
        "image_is_control": False,
        "return_control_map": False,
        "prompt": "a man walking in the snow",
        "ddim_steps": 25,
        "n_iter": 1,
        "model": model,
        "source_image": None,
        "source_processing": "txt2img",
    }
    horde = HordeLib()
    pil_image = horde.basic_inference(data)
    pil_image.save(
        f"images/stresstest/txt2img_{model}_{sampler}_{threading.current_thread().ident}_{i}.webp",
        quality=80,
    )


def run_iterations():
    for i in range(ITERATIONS):
        generate_images()


def main():
    global count
    count = 0
    threads = [
        threading.Thread(daemon=True, target=run_iterations),
        threading.Thread(daemon=True, target=run_iterations),
        threading.Thread(daemon=True, target=run_iterations),
        threading.Thread(daemon=True, target=run_iterations),
        threading.Thread(daemon=True, target=run_iterations),
    ]
    [x.start() for x in threads]
    [x.join() for x in threads if x]

    logger.warning(f"Test took {round(time.time() - start_time)} seconds ({count} generations)")


main()
