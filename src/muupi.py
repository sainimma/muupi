from MutantGenerator import *
from MuUtilities import *
from MuOperators import *
from MuAnalyzer import *
from astdump import *
from collections import namedtuple

import multiprocessing as mp
import argparse
import json

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--module-fullname', type=str, default=None,
                        help='Full name of module under test.')
    parser.add_argument('-p', '--module-path', type=str, default=None,
                        help='The path of source code of module under test.')
    parser.add_argument('-t', '--tsmodule-fullname', type=str, default=None,
                        help='Full name of test suite module.')
    parser.add_argument('-T', '--tsmodule-path', type=str, default=None,
                        help='The path of source code of test suite module.')
    parser.add_argument('-g', '--generator', type=str, default=None,
                        help='Specify a generator.')
    parser.add_argument('-P', '--generator-path', type=str, default=None,
                        help='Specify the path of a generator.')
    parser.add_argument('-l', '--list-generators', action='store_true',
                        help='List all available generators.')
    parser.add_argument('-c', '--create-files', action='store_true',
                        default=False, help='Create mutant .py source files')

    parser.add_argument('-o', '--mutation-operators', type=str, default=None,
                        help='Specify mutation operators to use.')
    parser.add_argument('--list-mutation-operators', action='store_true',
                        help='List all available mutation operators.')

    parsed_args = parser.parse_args(sys.argv[1:])
    return parsed_args, parser


def make_config(pargs, parser):
    # pdict = pargs.__dict__
    # return pdict

    pdict = pargs.__dict__
    # create a namedtuple object for fast attribute lookup
    key_list = pdict.keys()
    arg_list = [pdict[k] for k in key_list]
    Config = namedtuple('Config', key_list)
    nt_config = Config(*arg_list)
    return nt_config


def generator_factory(generator, path=None):
    if generator == "randomtester":
        randomtester = MuUtilities.load_module("generator.randomtester", path)
        return randomtester
    elif generator == "randombeam":
        return None
    elif generator == "bfsmodelchecker":
        return None
    elif generator == "dfsmodelchecker":
        return None
    else:
        return None


if __name__ == "__main__":

    parsed_args, parser = parse_args()
    config = make_config(parsed_args, parser)
    # print('Random testing using config={}'.format(config))

    suite_module = None
    module_under_test = None

    if config.list_generators:
        print "TODO: list all available generators."

    elif config.list_mutation_operators:
        print "Mutation Operators (shortname, fullname): "
        items = MutationOperator.list_all_operators()
        for i in xrange(1, len(items)+1):
            print str(i) + '. ' + items[i-1][0] + ': ' + items[i-1][1]
        print

    # load module to mutate
    elif config.module_fullname:
        print "Loading target module ...... "
        # todo: DO NOT REMOVE THE FOLLOWING TWO LINES
        # module_under_test_fullname = "sample.calculator"
        # module_under_test_path = "../sample/calculator.py"

        module_under_test_fullname = config.module_fullname
        module_under_test_path = config.module_path

        module_under_test = MuUtilities.load_module(module_under_test_fullname, module_under_test_path)
        unmutated_ast = MutantGenerator().parse(module_under_test)
        assert module_under_test is not None
        print "Done.\n"

        print "Loading mutation operators ...... "
        # build mutation operators:
        # 'None' means loading all mutation operators; or, select one or more from
        # ['AOD', 'AOR', 'ASR', 'BCR', 'LOD', 'LOI', 'CRP', 'EXS', 'LCR', 'BOD', 'BOR',
        # 'FHD', 'OIL', 'RIL', 'COR', 'SSIR', 'SEIR', 'STIR', 'SVD', 'ZIL']
        # The concrete definition of each mutation operator can be found in MuOperators.py
        if config.mutation_operators:
            operators = config.mutation_operators.split('+')
        else:
            operators = None
        mutation_operators = MutationOperator.build(operators)
        assert len(mutation_operators) > 0
        print "Done.\n"

        # DEBUG: print out the abstract syntax tree of target module
        # print_ast(original_tree)

        # generate mutants from target module
        print "Generating mutants from target module ...... "
        mutants = MutantGenerator().mutate(module=module_under_test, \
            operators=mutation_operators, output=config.create_files)
        print "Done.\n"

        if config.tsmodule_fullname and config.tsmodule_path:
            print "Loading test suite module ...... "
            # todo: DO NOT REMOVE THE FOLLOWING TWO LINES
            # suite_module_fullname = "sample.unittest_calculator"
            # suite_module_path = "../sample/unittest_calculator.py
            suite_module_fullname = config.tsmodule_fullname
            suite_module_path = config.tsmodule_path

            # Load test suite module
            suite_module = MuUtilities.load_module(suite_module_fullname, suite_module_path)
            print "Done.\n"

            # run a unit test suite on original sut
            print "Running unit test cases against target module before mutation ......"
            tester = MuTester()
            tester.load_test_suite_module(suite_module)
            tester.run()
            unmutated_test_results = tester.get_result()
            print "Test runs: " + str(unmutated_test_results.testsRun) \
                    + "; failures: " + str(len(unmutated_test_results.failures)) \
                    + "; errors: " + str(len(unmutated_test_results.errors))
            print "Done.\n"

            # if False or len(test_result.failures) > 0 or len(test_result.errors) > 0:
            #     print "Warning: current module to mutate failed in current unit test."
            # else:

            testers = []
            for mutant_module, mutant_ast, operator in mutants:
                tester = MuTester()
                tester.load_test_suite_module(suite_module)
                tester.set_mutant_module(mutated_module=mutant_module, original_module=module_under_test)
                testers.append(tester)

            results = []
            for tester in testers:
                tester.run()
                mutated_test_results = tester.get_result()
                results.append(mutated_test_results)

            json_metadata = []
            # iterate through the test results, and for each mutant extract its
            # metadata and store into JSON object
            for i in range(len(results)):
                # Gather all the data about the mutation
                mutant_module = mutants[i][0]
                mutant_ast = mutants[i][1]
                operator = mutants[i][2]
                mutated_test_results = results[i]
                # Get the killers for this mutant
                # An empty list implies no killers
                mutant_killers = MuAnalyzer.get_mutant_killers(unmutated_test_results, mutated_test_results)
                mutation = {}
                mutation["mutant_name"] = mutant_module.__name__
                mutation["mutated_ast_node"] = operator[0].__name__
                mutation["mutation_operator"] = operator[1].name()
                mutation["killed"] = False if (mutant_killers) else True
                mutation["killers"] = mutant_killers

                lineno = MuAnalyzer.get_lineno(mutant_ast, unmutated_ast)
                mutation["lineno"] = lineno[0]

                unmutated_output = MuAnalyzer.get_unmutated_output(module_under_test_fullname, module_under_test_path, lineno[0])
                mutation["unmutated_output"] = str(unmutated_output)

                mutated_line = MuAnalyzer.get_mutated_line(mutant_ast, lineno[0])
                mutation["mutated_line"] = str(mutated_line)

                json_metadata.append(json.dumps(mutation))

            # analyze test results
            print "Computing mutation score ......"
            MuAnalyzer.analyze(results)
            print "Done.\n"

            print "\n\n********** Mutation Test Done! **********\n"
