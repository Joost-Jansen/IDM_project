import numpy as np
import pickle
from itertools import cycle
from matplotlib import pyplot as plt
from datetime import date

from ope.envs.discrete_toy_mc import DiscreteToyMC
from ope.models.basics import BasicPolicy
from ope.experiment_tools.experiment import ExperimentRunner, analysis
from ope.experiment_tools.config import Config
from ope.utils import make_seed
from neurips_seeds import weighted_toymc_args, unweighted_toymc_args
from neurips_plotting import neurips_plot


def run(experiment_args):

    runner = ExperimentRunner()

    seeds  = []
    for t in range(experiment_args["num_trials"]): # Number of trials, config file for each trial.

        # Set random seed for trial.
        if experiment_args["seeds"] is None: seed = make_seed()
        else: seed = experiment_args["seeds"][t]
        seeds.append(seed)

        # For each trial, generate a single large dataset with the largest Nval.
        # For each Nval, we will compute the estimate for that value on the same dataset.
        max_Nval = max(experiment_args["Nvals"])

        # basic configuration with varying number of trajectories
        configuration = {
            "gamma": experiment_args["gamma"],
            "horizon": experiment_args["horizon"],
            "base_policy": experiment_args["p0"],
            "eval_policy": experiment_args["p1"],
            "stochastic_env": True,
            "stochastic_rewards": False,
            "sparse_rewards": False,
            "num_traj": max_Nval,
            "Nvals": experiment_args["Nvals"], # Compute value of estimate for these data sizes
            "is_pomdp": False,
            "pomdp_horizon": 2,
            "seed": seed,
            "experiment_number": 0,
            "access": 0,
            "secret": 0,
            "modeltype": "tabular",
            "to_regress_pi_b": False,
            "nstep_int": experiment_args["nstep_int"],
            "weighted": experiment_args["weighted"]
        }

        # store them
        cfg = Config(configuration)

        # initialize environment with this configuration
        env = DiscreteToyMC(n_left = 10, n_right = 10, random_start=True)

        # set seed for the experiment
        np.random.seed(cfg.seed)

        # processor processes the state for storage
        processor = lambda x: x

        # absorbing state for padding if episode ends before horizon is reached
        absorbing_state = processor(np.array([env.n_dim - 1]))

        # Setup policies
        actions = [0, 1]
        pi_e = BasicPolicy(
            actions, [max(.001, cfg.eval_policy), 1 - max(.001, cfg.eval_policy)])
        pi_b = BasicPolicy(
            actions, [max(.001, cfg.base_policy), 1 - max(.001, cfg.base_policy)])

        # add env, policies, absorbing state and processor
        cfg.add({
            'env': env,
            'pi_e': pi_e,
            'pi_b': pi_b,
            'processor': processor,
            'absorbing_state': absorbing_state
        })

        # Decide which OPE methods to run.
        # Currently only all is available
        cfg.add({'models': experiment_args["models"]})

        # Add the configuration
        runner.add(cfg)

    # Run the configurations
    results = runner.run()

    return results, {'seeds':seeds, 'args': experiment_args}


if __name__ == '__main__':
    # Run trials.
    unweighted_toymc_results = run(unweighted_toymc_args)
    weighted_toymc_results = run(weighted_toymc_args)

    # Plot
    neurips_plot(unweighted_toymc_results, "unweighted_toymc_plot")
    neurips_plot(weighted_toymc_results, "weighted_toymc_plot")


