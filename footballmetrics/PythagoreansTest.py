import Pythagoreans
import unittest

class PythagoreansTest(unittest.TestCase):
    testdict={'teams':['A','B','C', 'D'], 'pointsFor':[32, 65, 40, 0], 'pointsAgainst':[56,27,40, 79], \
              'wlp':[2/3., 1.0, 1/3., 0.0], 'nGames':3}
    
    testStringDict = {'teams':['A','B','C', 'D'], 'pointsFor':['bla', 65, 40, 0], 'pointsAgainst':[56,27,40, 79], \
              'wlp':[2/3., 1.0, 1/3., 0.0], 'nGames':3}
    
    testIncompleteDict = {'teams':['A','B','C', 'D']}
    
    # no optimization, used exponent: x = 2.63
    # calculated predictions and powers using the lambda's in iPython
    knownPredictions = {'Pythagorean':[0.18667076776695243,
                                       0.9097501086210673,
                                       0.5,
                                       0.0],
                        'Pythagenport':[0.18488954660887186,
                                        0.91329243205946342,
                                        0.5,
                                        0.0],
                        'PythagenportFO':[0.22587739319369521,
                                          0.87644280441932565,
                                          0.5,
                                          0.0],
                        'Pythagenpat':[0.18606512374956286,
                                       0.9126639951760125,
                                       0.5,
                                       0.0]}
    
    knownPowers = {'Pythagenport':[2.6510421261457591,
                                   2.6799998589388392,
                                   2.5889530984084219,
                                   2.5807587548561686],
                   'PythagenportFO':[2.2010421261457589,
                                     2.229999858938839,
                                     2.1389530984084217,
                                     2.1307587548561684],
                   'Pythagenpat':[2.6371372107309616,
                                  2.670996422565167,
                                  2.5659785768382335,
                                  2.556731811616984]}
        
    
    def testPythagoreanNoOptPrediction(self):
        '''Testing PythagoreanExpectation with known predictions...'''
        pyth = Pythagoreans.PythagoreanExpectation(self.testdict)
        pyth.calculatePythagorean(optimize=False, staticParams=[2.63])
        self.assertEqual(pyth.prediction, self.knownPredictions['Pythagorean'])
        
    def testPythagenportNoOptPrediction(self):
        '''Testing Pythagenport with known predictions...'''
        pyth = Pythagoreans.Pythagenport(self.testdict)
        pyth.calculatePythagorean(optimize=False, staticParams=[1.5, 0.45])
        self.assertEqual(pyth.prediction, self.knownPredictions['Pythagenport'])
        
    def testPythagenportFONoOptPrediction(self):
        '''Testing PythagenportFO with known predictions...'''
        pyth = Pythagoreans.PythagenportFO(self.testdict)
        pyth.calculatePythagorean(optimize=False, staticParams=[1.5])
        self.assertEqual(pyth.prediction, self.knownPredictions['PythagenportFO'])
        
    def testPythagenpatNoOptPrediction(self):
        '''Testing Pythagenpat with known predictions...'''
        pyth = Pythagoreans.Pythagenpat(self.testdict)
        pyth.calculatePythagorean(optimize=False, staticParams=[0.287])
        self.assertEqual(pyth.prediction, self.knownPredictions['Pythagenpat'])
        
    def testPythagenportNoOptPower(self):
        '''Testing Pythagenport with known powers...'''
        pyth = Pythagoreans.Pythagenport(self.testdict)
        pyth.calculatePythagorean(optimize=False, staticParams=[1.5, 0.45])
        self.assertEqual(pyth.power, self.knownPowers['Pythagenport'])
        
    def testPythagenportFONoOptPower(self):
        '''Testing PythagenportFO with known powers...'''
        pyth = Pythagoreans.PythagenportFO(self.testdict)
        pyth.calculatePythagorean(optimize=False, staticParams=[1.5])
        self.assertEqual(pyth.power, self.knownPowers['PythagenportFO'])
        
    def testPythagenpatNoOptPower(self):
        '''Testing Pythagenpat with known powers...'''
        pyth = Pythagoreans.Pythagenpat(self.testdict)
        pyth.calculatePythagorean(optimize=False, staticParams=[0.287])
        self.assertEqual(pyth.power, self.knownPowers['Pythagenpat'])
        
    
    def testPythagoreanOptNoParams(self):
        '''Testing Pythagorean without optimization and missing parameters...'''
        pyth = Pythagoreans.Pythagorean(self.testdict)
        self.assertRaises(TypeError, pyth.calculatePythagorean, optimize=False)
        
    def testPythagoreanBadInput(self):
        '''Testing Pythagorean with bad input...'''
        self.assertRaises(ValueError, Pythagoreans.Pythagorean, dataDict=self.testStringDict)
        
    def testPythagoreanIncompleteDict(self):
        '''Testing Pythagorean with incomplete dictionary...'''
        self.assertRaises(KeyError, Pythagoreans.Pythagorean, dataDict=self.testIncompleteDict)
        
    
if __name__ == "__main__":
    unittest.main()