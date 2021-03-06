from deepdiff import DeepDiff
from UserString import MutableString

import astor as ast

LINES_BEFORE = 5  # Number of lines before to include
LINES_AFTER = 5   # Number of lines after to include

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
    
    @classmethod
    def get_lineno(cls, mutant_ast, unmutated_ast):
        # Perform deep diff object comparison (see below for sample output)
        ddiff = DeepDiff(mutant_ast, unmutated_ast)

        if "type_changes" in ddiff:
            # Extract the attribute path (ex. root.body[0].body[4].body[0].value)
            # that is different between the two ASTs
            attributes = ddiff["type_changes"].keys()
            # Find and return the associated line number
            return cls.get_lineno_helper(mutant_ast, attributes)
        elif "iterable_item_added" in ddiff:
            return cls.get_lineno_helper(mutant_ast, ddiff["iterable_item_added"].keys())
        elif "iterable_item_removed" in ddiff:
            return cls.get_lineno_helper(mutant_ast, ddiff["iterable_item_removed"].keys())
        elif "values_changed" in ddiff:
            return cls.get_lineno_helper(mutant_ast, ddiff["values_changed"].keys())
        else:
            raise Exception("MuAnalyzer.get_lineno ERROR: Unhandled DeepDiff Type")

    @classmethod
    def get_lineno_helper(cls, mutant_ast, attributes):
        # List of differing line numbers between the two ASTs (usually only one)
        lineno = []

        for attribute in attributes:
            # NOTE: Making the extracted attribute path bounds more granular
            # *may* cause issues (since not all attributes have a lineno field)
            first_dot = attribute.index(".")
            last_dot = attribute.rindex("body") + 7
            
            # Execute string below based on attribute path to extract line number
            exec_str = "lineno = mutant_ast" + attribute[first_dot:last_dot] + ".lineno"
            locals_params = { 'lineno': 0, 'mutant_ast': mutant_ast }

            try:
                exec(exec_str, {}, locals_params)
                lineno.append(locals_params['lineno'])
            except:
                raise Exception("MuAnalyzer.get_lineno_helper ERROR: Could Not Extract lineno")
        
        return lineno

    @classmethod
    def get_lines(cls, source_ast, lineno):
        # NOTE: Converting mutant_ast to source removes blank lines (inside functions) and line comments,
        # including them in the source file may cuase line number inconsistencies
        # Have to add/subtract 1 at different points to account for zero based indexing
        code = ast.to_source(source_ast).split("\n")
        min_line = max(0, lineno - 1 - LINES_BEFORE)
        max_line = min(len(code), lineno + LINES_AFTER)
        return "\n".join(code[min_line : max_line]), min_line + 1

"""
--------------------
Example ddiff Output
--------------------
{
    'type_changes': {
        'root.body[0].body[4].body[0].value': {
            'new_type': <class'_ast.UnaryOp'>,
            'old_type': <class'_ast.Name'>,
            'old_value': <_ast.Nameobjectat0x04494D50>,
            'new_value': <_ast.UnaryOpobjectat0x04426FD0>
        }
    }
}
"""