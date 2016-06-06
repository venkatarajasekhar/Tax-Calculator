import os
import sys
import numpy as np
import pandas as pd
import pytest
CUR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(CUR_PATH, '..', '..'))
from taxcalc import Policy, Records, Calculator, Behavior

# use 1991 PUF-like data to emulate current puf.csv, which is private
TAXDATA_PATH = os.path.join(CUR_PATH, '..', 'altdata', 'puf91taxdata.csv.gz')
TAXDATA = pd.read_csv(TAXDATA_PATH, compression='gzip')
WEIGHTS_PATH = os.path.join(CUR_PATH, '..', 'altdata', 'puf91weights.csv.gz')
WEIGHTS = pd.read_csv(WEIGHTS_PATH, compression='gzip')


def test_incorrect_Behavior_instantiation():
    with pytest.raises(ValueError):
        behv = Behavior(behavior_dict=list())
    with pytest.raises(ValueError):
        behv = Behavior(num_years=0)
    with pytest.raises(ValueError):
        behv = Behavior(inflation_rates=list())


def test_correct_but_not_recommended_Behavior_instantiation():
    behv = Behavior(behavior_dict={})
    assert behv


def test_behavioral_response_Calculator():
    # create Records objects
    records_x = Records(data=TAXDATA, weights=WEIGHTS, start_year=2009)
    records_y = Records(data=TAXDATA, weights=WEIGHTS, start_year=2009)
    # create Policy objects
    policy_x = Policy()
    policy_y = Policy()
    # implement policy_y reform
    reform = {
        2013: {
            "_II_rt7": [0.496]
        }
    }
    policy_y.implement_reform(reform)
    # create two Calculator objects
    behavior_y = Behavior()
    calc_x = Calculator(policy=policy_x, records=records_x)
    calc_y = Calculator(policy=policy_y, records=records_y,
                        behavior=behavior_y)
    # vary substitution and income effects in calc_y
    behavior1 = {
        2013: {
            "_BE_sub": [0.4],
            "_BE_inc": [-0.15]
        }
    }
    behavior_y.update_behavior(behavior1)
    assert behavior_y.has_response()
    assert behavior_y.BE_sub == 0.4
    assert behavior_y.BE_inc == -0.15
    calc_y_behavior1 = calc_y.behavior.response(calc_x, calc_y)
    behavior2 = {
        2013: {
            "_BE_sub": [0.5],
            "_BE_inc": [-0.15]
        }
    }
    behavior_y.update_behavior(behavior2)
    calc_y_behavior2 = calc_y.behavior.response(calc_x, calc_y)
    behavior3 = {
        2013: {
            "_BE_sub": [0.4],
            "_BE_inc": [0.0]
        }
    }
    behavior_y.update_behavior(behavior3)
    calc_y_behavior3 = calc_y.behavior.response(calc_x, calc_y)
    # check that total income tax liability differs across the
    # three sets of behavioral-response elasticities
    assert (calc_y_behavior1.records._iitax.sum() !=
            calc_y_behavior2.records._iitax.sum() !=
            calc_y_behavior3.records._iitax.sum())


def test_correct_update_behavior():
    beh = Behavior(start_year=2013)
    beh.update_behavior({2014: {'_BE_sub': [0.5]},
                         2015: {'_BE_cg': [1.2]}})
    policy = Policy()
    should_be = np.full((Behavior.DEFAULT_NUM_YEARS,), 0.5)
    should_be[0] = 0.0
    assert np.allclose(beh._BE_sub, should_be, rtol=0.0)
    assert np.allclose(beh._BE_inc,
                       np.zeros((Behavior.DEFAULT_NUM_YEARS,)),
                       rtol=0.0)
    beh.set_year(2015)
    assert beh.current_year == 2015
    assert beh.BE_sub == 0.5
    assert beh.BE_inc == 0.0
    assert beh.BE_cg == 1.2


def test_incorrect_update_behavior():
    behv = Behavior()
    with pytest.raises(ValueError):
        behv.update_behavior({2013: {'_BE_inc': [+0.2]}})
    with pytest.raises(ValueError):
        behv.update_behavior({2013: {'_BE_sub': [-0.2]}})
    with pytest.raises(ValueError):
        behv.update_behavior({2013: {'_BE_cg': [-0.8]}})
    with pytest.raises(ValueError):
        behv.update_behavior({2013: {'_BE_xx': [0.0]}})
    with pytest.raises(ValueError):
        behv.update_behavior({2013: {'_BE_xx_cpi': [True]}})


def test_future_update_behavior():
    behv = Behavior()
    assert behv.current_year == behv.start_year
    assert behv.has_response() is False
    cyr = 2020
    behv.set_year(cyr)
    behv.update_behavior({cyr: {'_BE_cg': [1.0]}})
    assert behv.current_year == cyr
    assert behv.has_response() is True
    behv.set_year(cyr - 1)
    assert behv.has_response() is False


def test_behavior_default_data():
    paramdata = Behavior.default_data()
    assert paramdata['_BE_inc'] == [0.0]
    assert paramdata['_BE_sub'] == [0.0]
    assert paramdata['_BE_cg'] == [0.0]
