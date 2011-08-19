#
# Deals with gathering statistics from the sugarscape simulation.
#


class TimeVariableData():
    def __init__(self, size, default=0):
        self.data = [default for i in range(size)]

    def add(self, datum):
        self.data.append(datum)
        self.data = self.data[1:len(self.data)]



class Statistics():
    def __init__(self, sugarscape):
        self.sim = sugarscape
        
        self.current_tick = 0
        # the number of ticks in the past to record time variable data for
        self.record_ticks = 100

        self.num_agents_data = TimeVariableData(self.record_ticks, 0)
        self.agent_age_data  = TimeVariableData(self.record_ticks, 0)
        self.num_fertile_data = TimeVariableData(self.record_ticks, 0)
        self.num_births_data = TimeVariableData(self.record_ticks, 0)
        self.num_deaths_data = TimeVariableData(self.record_ticks, 0)
        self.mean_vision_data = TimeVariableData(self.record_ticks, 0)
        self.mean_sugar_metabolism_data = TimeVariableData(self.record_ticks, 0)
        self.mean_mates = TimeVariableData(self.record_ticks, 0)
        self.mean_children = TimeVariableData(self.record_ticks, 0)


    def tick(self):
        self.num_agents_data.add(self.sim.getNumAgents())
        self.num_deaths_data.add(self.sim.num_deaths)
        self.num_births_data.add(self.sim.num_births)

        num_agents = max(1, len(self.sim.agents))
        num_fertile = 0
        total_vision = 0.0
        total_sugar_metabolism = 0.0
        total_mates = 0.0
        total_children = 0.0

        for a in self.sim.agents:
            if a.isFertile():
                num_fertile += 1
            total_vision += a.vision
            total_sugar_metabolism += a.sugar_metabolism
            total_mates += len(a.mates)
            total_children += len(a.children)

        self.num_fertile_data.add(num_fertile)
        self.mean_vision_data.add(total_vision / num_agents)
        self.mean_sugar_metabolism_data.add(total_sugar_metabolism / num_agents)
        self.mean_mates.add(total_mates / num_agents)
        self.mean_children.add(total_children / num_agents)

        self.current_tick += 1


    def getTimePeriod(self):
        return self.current_tick-self.record_ticks, self.current_tick


    def getNumAgentsData(self):
        return self.num_agents_data.data

    def getAgentAgeData(self):
        return self.agent_age_data.data

    def getNumFertileData(self):
        return self.num_fertile_data.data

    def getNumDeathsData(self):
        return self.num_deaths_data.data

    def getNumBirthsData(self):
        return self.num_births_data.data

    def getMeanVisionData(self):
        return self.mean_vision_data.data

    def getMeanSugarMetabolismData(self):
        return self.mean_sugar_metabolism_data.data

    def getMeanMatesData(self):
        return self.mean_mates.data

    def getMeanChildrenData(self):
        return self.mean_children.data

