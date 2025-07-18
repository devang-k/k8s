"""
This module implements a Genetic Algorithm (GA) for optimizing the arrangement of polygons to minimize capacitance.
The GA includes functionalities for initializing a population, evaluating fitness, selection, crossover, mutation,
and convergence checking.

Classes:
- GAConfig: Configuration class for the Genetic Algorithm.
- Chromosome: Represents an individual in the population.
- GeneticAlgorithm: Encapsulates the functionalities of the Genetic Algorithm.

Functions:
- main: Entry point for running the Genetic Algorithm with command-line arguments.

Approach:
1. Initialize a population of random chromosomes.
2. Evaluate the fitness of each chromosome based on capacitance.
3. Select parents using rank selection.
4. Perform crossover and mutation to generate offspring.
5. Retain elite individuals and update the population.
6. Check for convergence and terminate if reached.
7. Output the best solution found.
"""

import random
from os import makedirs
from os.path import exists, join
import time
import argparse
import json
from dataclasses import dataclass
from genetic_algorithm.state_generator import StateGenerator
from gdsast import gds_write
import logging

logger = logging.getLogger('sivista_app')

@dataclass
class GAConfig:
    """Configuration for the Genetic Algorithm."""
    pop_size: int = 100
    max_generations: int = 100
    elite_size: int = 2
    mutation_rate: float = 0.1
    convergence_threshold: float = 1e-3
    convergence_generations: int = 10
    min_gene_value: int = 0
    max_gene_value: int = 5
    cell: str = 'MUX21X1'
    model_type: str = 'gnn'
    tech: str = './tech/monCFET/monCFET.tech'
    pdk: str = 'monCFET'
    netlist: str = ''
    output_folder: str = ''

    def __post_init__(self):
        """Post-initialization to set dependent paths."""
        # self.netlist = f'./tech/{self.pdk}/{self.pdk}.spice'
        # self.output_folder = f'./genetic_algorithm/output/{self.cell}'

class Chromosome:
    """Represents an individual in the population."""
    def __init__(self, genes):
        """Initializes a Chromosome with genes and fitness.

        Args:
            genes (list): List of Y-values for each polygon (indexed by polygon ID).
        """
        self.genes = genes
        self.fitness = None  # Fitness value of the chromosome

class GeneticAlgorithm:
    """Genetic Algorithm class encapsulating all functionalities."""
    def __init__(self, state_generator: StateGenerator, config: GAConfig):
        """Initializes the Genetic Algorithm with a state generator and configuration.

        Args:
            state_generator (StateGenerator): State generator for calculating capacitance.
            config (GAConfig): Configuration for the Genetic Algorithm.
        """
        self.state_generator = state_generator
        self.pop_size = config.pop_size
        self.max_generations = config.max_generations
        self.elite_size = config.elite_size
        self.mutation_rate = config.mutation_rate
        self.convergence_threshold = config.convergence_threshold
        self.convergence_generations = config.convergence_generations
        self.min_gene_value = config.min_gene_value
        self.max_gene_value = config.max_gene_value
        self.population = []
        self.best_fitness_history = []
        self.best_individual = None

    def calculate_capacitance(self, genes):
        """Calculates the capacitance based on the given genes (arrangement of polygons).

        Args:
            genes (list): List of Y-values for each polygon.

        Returns:
            float: Calculated capacitance.
        """
        return self.state_generator.getCapacitance(genes)

    def initialize_population(self):
        """
        Initializes the population with random chromosomes.
        Each gene (Y-value) is a random integer between min_gene_value and max_gene_value.
        """
        state = self.state_generator.getState()
        logger.debug(f"[GA-LOG] state in initialize {state}")
        num_of_polygons = len(state)
        population = []
        for _ in range(self.pop_size):
            genes = [
                random.randint(self.min_gene_value, self.max_gene_value)
                for _ in range(num_of_polygons)
            ]
            chromosome = Chromosome(genes)
            population.append(chromosome)
        self.population = population

    def evaluate_fitness(self, chromosome):
        """Evaluates the fitness of a chromosome.
        
        Args:
            chromosome (Chromosome): The chromosome to evaluate.

        Returns:
            bool: True if the chromosome passes the DRC check, False otherwise.
        """
        if self.state_generator.getDrc(chromosome.genes):
            capacitance_data = self.calculate_capacitance(chromosome.genes)[0]
            capacitance_list = capacitance_data.drop(columns=['File']).values.flatten()
            capacitance = sum(capacitance_list)
            # Fitness is inversely proportional to capacitance (since we want to minimize it)
            chromosome.fitness = 1 / (1 + capacitance)  # Add 1 to avoid division by zero

            logger.debug("*******************************************************")
            logger.debug("\n")
            logger.debug("GA-LOG")
            logger.debug("\n")
            logger.debug("\n")
            logger.debug(f"Capacitance: {capacitance_list}")
            logger.debug(f"Capacitance Sum: {capacitance}")
            logger.debug(f"Fitness: 1/(1+{capacitance}) = {chromosome.fitness}")
            logger.debug("\n")
            logger.debug("*******************************************************")
            return True
        else:
            return False

    def rank_selection(self):
        """ Performs rank selection on the population.
        Individuals are ranked based on fitness, and selection probabilities are assigned
        accordingly to favor higher-ranked individuals.

        Returns:
            Chromosome: Selected individual based on rank.
        """
        # Sort population by fitness in descending order
        sorted_population = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        n = len(sorted_population)
        total_rank = n * (n + 1) / 2  # Sum of ranks

        # Assign selection probabilities based on rank
        selection_probs = [(n - rank) / total_rank for rank in range(n)]

        # Generate cumulative probabilities
        cumulative_probs = []
        cumulative = 0
        for prob in selection_probs:
            cumulative += prob
            cumulative_probs.append(cumulative)

        # Select an individual based on cumulative probabilities
        r = random.random()
        for i, individual in enumerate(sorted_population):
            if r <= cumulative_probs[i]:
                return individual
        return sorted_population[-1]  # Return the last individual if none selected

    def single_point_crossover(self, parent1, parent2):
        """Performs single-point crossover between two parents to produce two offspring.

        Args:
            parent1 (Chromosome): First parent chromosome.
            parent2 (Chromosome): Second parent chromosome.

        Returns:
            tuple: Two offspring chromosomes.
        """
        num_genes = len(parent1.genes)
        if num_genes > 1:
            crossover_point = random.randint(1, num_genes - 1)
        else:
            crossover_point = 1  # If only one gene, crossover at position 1
        child1_genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
        child2_genes = parent2.genes[:crossover_point] + parent1.genes[crossover_point:]
        child1 = Chromosome(child1_genes)
        child2 = Chromosome(child2_genes)
        return child1, child2

    def mutation(self, chromosome):
        """Applies mutation to a chromosome.

        Args:
            chromosome (Chromosome): The chromosome to mutate.
        """
        for i in range(len(chromosome.genes)):
            if random.random() < self.mutation_rate:
                chromosome.genes[i] = random.randint(self.min_gene_value, self.max_gene_value)

    def run(self):
        """Executes the genetic algorithm.

        Returns:
            tuple: Best genes and their corresponding capacitance.
        """
        # Initialize population
        self.initialize_population()
        valid_population = []
        # Evaluate initial population
        for chromosome in self.population:
            if self.evaluate_fitness(chromosome):
                valid_population.append(chromosome)

        self.population = valid_population

        generation = 0
        convergence_counter = 0
        prev_best_fitness = None

        while generation < self.max_generations:
            generation += 1
            new_population = []
            if not self.population:
                logger.debug("[GA-LOG] No Valid Chromosome. End evolution.")
            # Elitism: retain top individuals
            sorted_population = sorted(self.population, key=lambda x: x.fitness, reverse=True)
            elites = sorted_population[:self.elite_size]
            new_population.extend(elites)

            # Generate new offspring
            while len(new_population) < self.pop_size:
                # Selection
                parent1 = self.rank_selection()
                parent2 = self.rank_selection()
                # Crossover
                child1, child2 = self.single_point_crossover(parent1, parent2)
                # Mutation
                self.mutation(child1)
                self.mutation(child2)
                if self.evaluate_fitness(child1):
                    new_population.append(child1)
                if len(new_population) < self.pop_size and self.evaluate_fitness(child2):
                    new_population.append(child2)

            # Update population
            self.population = new_population

            # Record best fitness
            best_chromosome = max(self.population, key=lambda x: x.fitness)
            best_fitness = best_chromosome.fitness
            self.best_fitness_history.append(best_fitness)
            logger.debug(f"[GA-LOG] Generation {generation}: Best Fitness = {best_fitness:.6f}")

            # Check convergence
            if prev_best_fitness and abs(best_fitness - prev_best_fitness) < self.convergence_threshold:
                convergence_counter += 1
            else:
                convergence_counter = 0
            prev_best_fitness = best_fitness

            if convergence_counter >= self.convergence_generations:
                logger.debug("[GA-LOG] Convergence reached.")
                break

        # After evolution, find the best solution
        if self.population:
            self.best_individual = max(self.population, key=lambda x: x.fitness)
            logger.debug("\n [GA-LOG] Best solution found:")
            logger.debug(f"[GA-LOG] Genes (Y-values): {self.best_individual.genes}")
            logger.debug(f"[GA-LOG] Fitness: {self.best_individual.fitness:.6f}")
            best_capacitance = self.calculate_capacitance(self.best_individual.genes)
            logger.debug(f"[GA-LOG] Capacitance: {best_capacitance}")
            return self.best_individual.genes, best_capacitance
        else:
            logger.debug("[GA-LOG] No solution found.")
            return None, None

def main(args):
    """Main function to run the Genetic Algorithm with command-line arguments.

    Args:
        args (dict): Command-line arguments.
    """
    # Create GAConfig instance with command-line arguments
    config = GAConfig(
        pop_size=args.get('pop_size', 100),
        max_generations=args.get('max_generations', 100),
        elite_size=args.get('elite_size', 2),
        mutation_rate=args.get('mutation_rate', 0.1),
        convergence_threshold=args.get('convergence_threshold', 1e-3),
        convergence_generations=args.get('convergence_generations', 10),
        min_gene_value=args.get('min_gene_value', 0),
        max_gene_value=args.get('max_gene_value', 5),
        cell=args.get('cell', 'MUX21X1'),
        model_type=args.get('model_type', 'gnn'),
        tech=args.get('tech', './tech/monCFET/monCFET.tech'),
        pdk=args.get('pdk', 'monCFET'),
        output_folder=args.get("output_folder", ''),
        netlist=args.get("netlist", '')
    )
    
    # Load configurations from a JSON file if provided
    if args.get('config'):
        with open(args.get('config'), 'r') as f:
            config_dict = json.load(f)
            for key, value in config_dict.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    print(f"Ignoring unknown configuration key: {key}")

    logger.debug("tech data")

    # Initialize the StateGenerator
    state_generator = StateGenerator(
        config.cell,
        config.model_type,
        config.tech,
        config.netlist,
        config.output_folder
    )
    
    # Get the initial capacitance for comparison
    initial_genes = state_generator.getState()
    initial_capacitance_df = state_generator.getCapacitance(initial_genes)[0]  # Extract the DataFrame
    initial_capacitance = initial_capacitance_df.drop(columns=['File']).values.flatten().mean()  # Average the values

    # Run the Genetic Algorithm
    start_time = time.time()
    ga = GeneticAlgorithm(state_generator, config)
    best_genes, final_capacitance_df = ga.run()
    final_capacitance = final_capacitance_df[0].drop(columns=['File']).values.flatten().mean()  # Average the values
 
    file_name = f"{''.join(map(str, best_genes))}_1_RT_6_1"
    newgdsJson = ga.state_generator.getData(best_genes)
    if not exists(config.output_folder):
        makedirs(config.output_folder)

    # Write the GDS file to the correct path
    output_file_path = join(config.output_folder, f"best_state_{file_name}.gds")
    with open(output_file_path, "wb") as f:
        gds_write(f, newgdsJson)
    end_time = time.time()

    # Output results
    logger.debug(f"\n[GA-LOG] Total time taken: {end_time - start_time:.3f} seconds")
    logger.debug(f"[GA-LOG] Best genes: {best_genes}")
    logger.debug(f"[GA-LOG] Initial capacitance: {initial_capacitance}")
    logger.debug(f"[GA-LOG] Final capacitance: {final_capacitance}")
    improvement = initial_capacitance - final_capacitance
    logger.debug(f"[GA-LOG] Improvement: {improvement}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Genetic Algorithm Optimization Script')
    parser.add_argument('--cell', type=str, default='MUX21X1', help='Cell name')
    parser.add_argument('--netlist', type=str)
    parser.add_argument('--model_type', type=str, default='gnn', choices=['moe', 'gnn'], help='Model type')
    parser.add_argument('--tech', type=str, default='./tech/monCFET/monCFET.tech', help='Technology file path')
    parser.add_argument('--pdk', type=str, default='monCFET', help='PDK name')
    parser.add_argument('--pop_size', type=int, default=100, help='Population size for the GA')
    parser.add_argument('--max_generations', type=int, default=10, help='Maximum number of generations')
    parser.add_argument('--elite_size', type=int, default=2, help='Number of elite individuals')
    parser.add_argument('--mutation_rate', type=float, default=0.1, help='Mutation rate')
    parser.add_argument('--convergence_threshold', type=float, default=1e-6, help='Convergence threshold')
    parser.add_argument('--convergence_generations', type=int, default=20, help='Generations for convergence check')
    parser.add_argument('--min_gene_value', type=int, default=0, help='Minimum gene value')
    parser.add_argument('--max_gene_value', type=int, default=5, help='Maximum gene value')
    parser.add_argument('--config', type=str, help='Path to configuration JSON file')
    parser.add_argument('--output_folder')
    args, unknown = parser.parse_known_args()
    args = {
        "cell":args.cell,
        "model_type":args.model_type,
        "tech":args.tech,
        "pdk":args.pdk,
        "pop_size":args.pop_size,
        "max_generations":args.max_generations,
        "elite_size":args.elite_size,
        "mutation_rate":args.mutation_rate,
        "convergence_threshold":args.convergence_threshold,
        "convergence_generations":args.convergence_generations,
        "min_gene_value":args.min_gene_value,
        "max_gene_value":args.max_gene_value,
        "netlist":args.netlist,
        "output_folder":args.output_folder
      
    }



    main(args)
