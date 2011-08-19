class AbstractCulture():
    GROUPS = []
    COLORS = {}

    def __init__(self, agent, world, rand):
        self.agent = agent
        self.world = world
        self.rand = rand

    def update(self):
        pass

    def flip(self, tag):
        pass

    def getGroup(self):
        return ""



class BasicCulture(AbstractCulture):
    GROUPS = ["blue", "red"]
    COLORS = {
        "blue" : (0.0, 0.0, 1.0, 1.0),
        "red"  : (1.0, 0.0, 0.0, 1.0),
    }

    def __init__(self, agent, world, rand):
        AbstractCulture.__init__(self, agent, world, rand)


    def update(self):
        tags = self.agent.culture_tags
        for n in self.world.getNeighbourAgents(self.agent.x, self.agent.y):
            #tag_index = rand.randint(0, min(len(n.culture.tags), len(self.tags)))
            tag_index = self.rand.randint(0, len(self.agent.culture_tags) - 1)
            if tags[tag_index] != n.culture_tags[tag_index]:
                n.culture.flip(tag_index)


    def flip(self, tag):
        tags = self.agent.culture_tags

        if 0 <= tag < len(tags):
            t = tags[tag]
            if t == 0:
                tags[tag] = 1
            else:
                tags[tag] = 0


    def getGroup(self):
        num0 = num1 = 0
        for t in self.agent.culture_tags:
            if t == 0:
                num0 += 1
            else:
                num1 += 1

        if num0 > num1:
            return "blue"
        return "red"



