

class MuAnalyzer(object):

    @classmethod
    def analyze(cls, results):
        """
        Analyzes a test result, computes mutation scores, and makes a final test report.
        """
        if len(results) == 0:
            return
        # number of killed mutants
        mutant_killed = 0
        # total number of mutants
        mutant_total = len(results)

        for result in results:
            if len(result.failures) > 0 or len(result.errors) > 0:
                mutant_killed += 1

        mutation_score = mutant_killed * 1.0 / mutant_total
        print "\n\nmutation score: " + str(mutation_score)

    @classmethod
    def get_mutant_killers(cls, unmutated_test_results, mutated_test_results):
        """
        Analyzes an unmutated module's test results and the mutated module's test results
        Returns a list of 2-tuples consisting of the name of the mutant killing test and the Exception Trace
        Returns an empty list if no mutant killers
        """
        result = []
        for failure in mutated_test_results.failures:
            if failure not in unmutated_test_results.failures:
                result.append((failure, mutated_test_results.failures[failure]))
        return result

