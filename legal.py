import matplotlib.pyplot as plt
from scipy.stats import powerlaw
import numpy as np
from numpy import loadtxt
import matplotlib.pyplot as plot
import time
import locale

class PerfTimer:
    def __init__(self, enabled):
        self.start_time = time.time()
        self.enabled = enabled

    def progress(self, text):
        if self.enabled:
            print(text, time.time() - self.start_time, "milliseconds")
            self.start_time = time.time()

# Enable performance tracking or not
c = PerfTimer(False)
locale.setlocale( locale.LC_ALL, '' )

simulations = 10000
if simulations != 1000000:
    print ("Running with dev simulations. Switch to 1M for prod.")


# Elicitation Values

lawyers_min, lawyers_max = 1, 5         # What's the minimum and maximum amount of lawyers you'd
                                        # expect to be working on the disclosure of a breach?
lawyer_rate_average   = 350             # What's the average rate for your lawyers? How much does it vary?
lawyer_rate_variance  = 50
disclosure_lawyer_hours_min = 8
disclosure_lawyer_hours_max = 160       # How many hours could each lawyer spend on getting disclosure done?

engineers_min, engineers_max = 0, 5     # How many engineers might it take to disclose the breach publicly?

engineer_pay_min = 200000 / 2080        # Minimum engineer cost per hour. Average salary / hours per year.
engineer_pay_max = 634694 / 2080        # Maximum engineer cost per hour. Revenue per employee / hours per year.

disclosure_lawyer_hours_min = 8         # Minimum amount of time an engineer might work on the disclosure project
disclosure_lawyer_hours_max = 40        # Maximum amount of time an engineer might work on the disclosure project

litigation_probability_yes = .25
litigation_probability_no = .75         # Probability that litigation will, will not happen. Must equal 1.

litigants_min, litigants_max = 1, 10    # Reasonable number of litigants attracted towards a disclosed breach.

discovery_probability_yes = .80
discovery_probability_no  = .20         # Probability that discovery will, will not happen. Must equal 1.

discovery_gigabytes_min = 10
discovery_gigabytes_max = 1000          # How much data will have to go through eDiscovery review

discovery_gigabytes_cost_min = 12000
discovery_gigabytes_cost_max = 30000    # Cost per gigabye of eDiscovery review

litigation_flat_fee = 200000            # An assumption that "Going to trial" is a (quite large) flat fee predetermined by your legal team and counsel.
                                        # However, if this is not figured out, the costs are hourly and unbridled.
                                        # Especially in multi-year trials, and you'd need to model it with that uncertainty.
                                        # This Monte Carlo _does not_ model this!

trial_odds_yes = .05
trial_odds_no  = .95                    # Odds of going to trial.

regulation_odds_yes = .05               # Odds of having an audit requirement imposed.
regulation_odds_no  = .95               # This can be modeled further, to include several other costs we are leaving out.


# Statistical Values

settlements = loadtxt('settlements.dat')    # Loading in external data for settlements
fit = powerlaw.fit(settlements)             # Fitting data to a simulated Power Law, which we think is reasonable.

incidents = powerlaw(
    a=fit[0],
    loc=fit[1],
    scale=fit[2]
)

c.progress("Disclosure Legal")

# Disclosure complexity (Legal)
# (Lawyers * Lawyer Rate * Hours) + (Engineers * Eng Pay * Hours)
disclosure_lawyers      = np.random.uniform(lawyers_min, lawyers_max, simulations)     # What's the minimum? What's the maximum?
disclosure_lawyer_rate  = np.random.normal(lawyer_rate_average, lawyer_rate_variance, simulations)  # Using https://thervo.com/costs/attorney-fees as stand-in data
disclosure_lawyer_hours = np.random.uniform(disclosure_lawyer_hours_min, disclosure_lawyer_hours_max, simulations)   # At least a day per lawyer, as much as several weeks

disclosure_legal_costs  = np.multiply(
    np.multiply(
        disclosure_lawyers, disclosure_lawyer_rate),
    disclosure_lawyer_hours)                                      # Disclosure Legal Total Cost

c.progress("Disclosure Eng")
# Disclosure complexity (Engineering)
disclosure_engineers        = np.random.uniform(engineers_min, engineers_max, simulations)
disclosure_engineers_pay    = np.random.uniform(engineer_pay_min, engineer_pay_max, simulations)
disclosure_engineers_hours  = np.random.uniform(disclosure_lawyer_hours_min, disclosure_lawyer_hours_max, simulations)

disclosure_engineer_costs = np.multiply(
    np.multiply(
        disclosure_engineers, disclosure_engineers_pay),
    disclosure_engineers_hours)                                                         # Disclosure Engineer costs

c.progress("Litigation Event")
litigation_event = np.random.choice([1, 0], simulations, p=[litigation_probability_yes, litigation_probability_no])  # Will litigation happen?

litigants = np.random.uniform(litigants_min, litigants_max, simulations)                        # How many litigants would need to be consolidated? (Class Action)


multiple_litigant_costs = np.multiply(                                  # Did litigation even happen? If so, how many litigants? Then, multiply a lawyer fee for a day of work merging each litigant. This seems conservative.
    np.multiply(
        litigation_event, litigants),
    disclosure_lawyer_rate * 8)

c.progress("Discovery")
# Discovery?
discovery_event = np.random.choice([1, 0], simulations, p=[discovery_probability_yes, discovery_probability_no])     # Elicit: We are being sued, we have been served. How likely is discovery?

discovery_gigabytes = np.random.uniform(discovery_gigabytes_min, discovery_gigabytes_max, simulations)             # Typical amount of gigabytes to process in discovery
discovery_gigabytes_costs = np.random.uniform(discovery_gigabytes_cost_min, discovery_gigabytes_cost_max, simulations)  # Cost per gigabyte of analysis. Fluctuates greatly based on internal tooling

discovery_costs = np.multiply(litigation_event,np.multiply(
    np.multiply(
        discovery_event, discovery_gigabytes),
    discovery_gigabytes_costs))                                            # Discovery Costs

c.progress("Settlement")
# Settlement - We assume there will be one.
settlement_costs = np.multiply(litigation_event,incidents.rvs(simulations)) # Just grabbing settlements from our power law data simulating our data.
                                                                            # In the future, we can build a different power law based on elicitation from a point of view.

# Trial


c.progress("Trial")
litigation_event = np.random.choice([1, 0], simulations, p=[trial_odds_yes, trial_odds_no])      # <- Most settlements happen before trial. What are the odds we go to trial

litigation_costs = np.multiply(                                             # Costs. Did the event happen, if so, flat fee.
    litigation_event, np.full(
        simulations, litigation_flat_fee)
    )

c.progress("Regulation")
# Regulation
regulation_event = np.random.choice([1, 0], simulations, p=[regulation_odds_yes, regulation_odds_no])      # Did we get hit with a audit requirement?

audit_fee = np.random.choice(                                               # Did we get hit with a one-time audit, or ten years of auditing?
    [250 * 80 * 2, 250 * 80 * 2 * 10],                                      # Typical audit cost from bay area firms (2 person 2 week)
    1,
    simulations,
    p=[.90, .10]
)

regulation_costs = np.multiply(                                             # Regulation costs
    litigation_event, np.multiply(                                          # If no litigation (0), no regulation
        regulation_event, audit_fee)                                        # if regulation, one audit or ten?
)

# Indemnification - Skipping
    # Model any indemnification costs here

# Final Cost
cost = []

c.progress("Totals")
for n in range(simulations):

    cost.append(disclosure_legal_costs[n]+ disclosure_engineer_costs[n] + multiple_litigant_costs[n] + discovery_costs[n] + settlement_costs[n] + litigation_costs[n] + regulation_costs[n])

c.progress("Build Histogram")
plot.hist(cost, bins='auto')

c.progress("Show Histogram")
plot.show()

c.progress("Stats")
print("Min", locale.currency(np.min(cost),grouping=True ))
print("Max", locale.currency(round(np.max(cost)),grouping=True))
print("STD", locale.currency(round(np.std(cost)),grouping=True ))
print("Mean", locale.currency(round(np.mean(cost)),grouping=True ))
print("Median", locale.currency(round(np.median(cost)),grouping=True ))
print("5%/95% Confidence Interval", locale.currency(round(np.percentile(cost, 5)), grouping=True ), "-" , locale.currency(round(np.percentile(cost, 95)), grouping=True ))

c.progress("Finished")
