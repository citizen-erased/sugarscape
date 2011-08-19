import copy, util
from culture import BasicCulture

class Agent():
    def __init__(self, world, **kwargs):
        self.world = world
        self.rand = world.rand
        self.dead = False
        self.age = 0
        self.death_cause = "none"
        self.children = []
        self.mates = []

        self.x                  = kwargs.get("x", 0)
        self.y                  = kwargs.get("y", 0)
        self.sugar_metabolism   = kwargs.get("sugar_metabolism", 1)
        self.spice_metabolism   = kwargs.get("spice_metabolism", 1)
        self.vision             = kwargs.get("vision", 1)
        self.max_age            = kwargs.get("max_age", 80)
        self.gender             = kwargs.get("gender", "male")
        self.fertile_age_start  = kwargs.get("fertile_age_start", 15)
        self.fertile_age_end    = kwargs.get("fertile_age_end", 50)

        self.initial_sugar      = kwargs.get("sugar", 1)
        self.sugar              = kwargs.get("sugar", 1)
        self.initial_spice      = kwargs.get("spice", 1)
        self.spice              = kwargs.get("spice", 1)

        self.culture_tags       = kwargs.get("culture_tags", [0])
        self.culture_type       = kwargs.get("culture", "BasicCulture")

        self.immune_sys         = kwargs.get("immune_sys", [])
        self.initial_immune_sys = copy.deepcopy(self.immune_sys)

        self.diseases = []
        for d in kwargs.get("diseases", []):
            self.infect(d)

        self.sugar_metabolism = float(self.sugar_metabolism)
        self.spice_metabolism = float(self.spice_metabolism)


        if self.culture_type == "BasicCulture":
            self.culture = BasicCulture(self, self.world, self.rand)


    def tick(self):
        if self.age >= self.max_age:
            self.dead = True
            self.death_cause = "age"
            self.distributeWealth()
            return

        sugar_m = self.getTotalSugarMetabolism()
        sugar_consumed = min(self.sugar, sugar_m)
        self.sugar -= sugar_m
        self.world.addSugarMetabolismPollution(self.x, self.y, sugar_consumed)

        if self.sugar < 0.0:
            self.dead = True
            self.death_cause = "sugar starvation"
            return

        spice_m = self.getTotalSpiceMetabolism()
        spice_consumed = min(self.spice, spice_m)
        self.spice -= spice_m
        self.world.addSpiceMetabolismPollution(self.x, self.y, spice_consumed)

        if self.spice < 0.0:
            self.dead = True
            self.death_cause = "spice starvation"
            return

        self.age += 1
        self.move()
        self.culture.update()
        self.immuneResponse()
        self.infectNeighbours()
        self.reproduce()


    def distributeWealth(self):
        if not self.children:
            return

        sugar = self.sugar / len(self.children)
        spice = self.spice / len(self.children)
        for c in self.children:
            c.sugar += sugar
            c.spice += spice


    def getTotalSugarMetabolism(self):
        m = 0
        for d in self.diseases:
            m += d.extra_sugar
        return self.sugar_metabolism + m


    def getTotalSpiceMetabolism(self):
        m = 0
        for d in self.diseases:
            m += d.extra_spice
        return self.spice_metabolism + m


    def move(self):
        # create a list of tiles to check out, one list for each axis of vision.
        # tiles ordered from nearst to furthers.
        dirs = []
        dirs.append([(self.x, self.y+y+1) for y in range(self.vision)])
        dirs.append([(self.x, self.y-y-1) for y in range(self.vision)])
        dirs.append([(self.x+x+1, self.y) for x in range(self.vision)])
        dirs.append([(self.x-x-1, self.y) for x in range(self.vision)])

        # shuffle so the order each direction to be checked is random
        self.rand.shuffle(dirs)

        # Set the best move to the current agent location as an agent shouldn't
        # move if its  current location is the best one.
        x1, y1 = self.x, self.y
        best_location = (x1, y1)
        best_location_value = self.rateTile(x1, y1)
        distance = 0

        # Check for the best tile to move to.
        #
        # A tile is rejected if it is occupied or its rating is less than the
        # best one found so far.
        for dir_array in dirs:
            for d in dir_array:
                x2, y2 = d[0], d[1]

                if self.world.isTileOccupied(x2, y2):
                    continue

                value = self.rateTile(x2, y2)
                dist = (x2-x1 * x2-x1) + (y2-y1 * x2-y1)

                if value > best_location_value or (value == best_location_value and dist < distance):
                    best_location_value = value
                    best_location = d
                    distance = dist


        # move to the best location found (this could be the same location the
        # agent is currently in)
        self.x, self.y = self.world.updateAgentPosition(self, self.x, self.y, best_location[0], best_location[1])

        # harvest
        self.sugar += self.world.harvestSugarAt(self.x, self.y)
        self.spice += self.world.harvestSpiceAt(self.x, self.y)


    def rateTile(self, x, y):
        # welfare formula form p.97
        m1, m2 = self.getTotalSugarMetabolism(), self.getTotalSpiceMetabolism()
        mt = m1 + m2

        w1 = self.sugar + self.world.getSugarAt(x, y)
        w2 = self.spice + self.world.getSpiceAt(x, y)
        W = (w1 ** (m1/mt)) * (w2 ** (m2/mt))

        p = self.world.getPollutionAt(x, y)

        return W / (1.0+p)
        #sugar = self.world.getSugarAt(x, y)
        #spice = self.world.getSpiceAt(x, y)
        #p = self.world.getPollutionAt(x, y)
        #return s / (1.0+p)


    def reproduce(self):
        if not self.isFertile():
            return

        # choose neighbouring agents at random
        ns = self.world.getNeighbourAgents(self.x, self.y)
        self.rand.shuffle(ns)

        for a in ns:
            if not self.isFertile():
                break

            if not a.isFertile():
                continue

            # Find the empty tiles around both agents. One empty tile is
            # required to create a child.
            empty_tiles = self.world.getEmptyNeighbourTiles(self.x, self.y) + self.world.getEmptyNeighbourTiles(a.x, a.y)

            if not empty_tiles:
                continue

            # set the mother and father agents
            mother = self if self.gender == "female" else a
            father = self if self.gender == "male" else a

            r = self.rand
            args = {}

            # the child can be born in any of the empty tiles
            position = self.rand.choice(empty_tiles)
            args["x"] = position[0]
            args["y"] = position[1]

            # set child properties based on some inheritance rules
            #args["sugar_metabolism"] = r.choice((mother.sugar_metabolism, father.sugar_metabolism))
            #args["spice_metabolism"] = r.choice((mother.spice_metabolism, father.spice_metabolism))
            #args["vision"] = r.choice((mother.vision, father.vision))
            #args["max_age"] = r.choice((mother.max_age, father.max_age))

            # set child properties based on inheritance and mutation
            vis = r.choice((mother.vision, father.vision))
            if r.randint(0, self.world.vision_mutation_chance) == 0:
                vis += r.choice((-1, 1)) * r.randint(self.world.vision_mutation_range[0], self.world.vision_mutation_range[1])
            args["vision"] = util.clamped(self.world.global_vision_range[0], self.world.global_vision_range[1], vis)

            sugar_m = r.choice((mother.sugar_metabolism, father.sugar_metabolism))
            if r.randint(0, self.world.sugar_metabolism_mutation_chance) == 0:
                sugar_m += r.choice((-1, 1)) * r.randint(self.world.sugar_metabolism_mutation_range[0], self.world.sugar_metabolism_mutation_range[1])
            args["sugar_metabolism"] = util.clamped(self.world.global_sugar_metabolism_range[0], self.world.global_sugar_metabolism_range[1], sugar_m)

            spice_m = r.choice((mother.spice_metabolism, father.spice_metabolism))
            if r.randint(0, self.world.spice_metabolism_mutation_chance) == 0:
                spice_m += r.choice((-1, 1)) * r.randint(self.world.spice_metabolism_mutation_range[0], self.world.spice_metabolism_mutation_range[1])
            args["spice_metabolism"] = util.clamped(self.world.global_spice_metabolism_range[0], self.world.global_spice_metabolism_range[1], spice_m)

            age = r.choice((mother.max_age, father.max_age))
            if r.randint(0, self.world.age_mutation_chance) == 0:
                age += r.choice((-1, 1)) * r.randint(self.world.age_mutation_range[0], self.world.age_mutation_range[1])
            args["max_age"] = util.clamped(self.world.global_age_range[0], self.world.global_age_range[1], age)

            # set child's gender
            args["gender"] = r.choice(("male", "female"))

            if args["gender"] == "male":
                args["fertile_age_start"] = mother.fertile_age_start
                args["fertile_age_end"] = mother.fertile_age_end
            else:
                args["fertile_age_start"] = father.fertile_age_start
                args["fertile_age_end"] = father.fertile_age_end

            # each parent gives half their initial sugar to the child as its
            # birth sugar.
            args["sugar"] = (mother.initial_sugar / 2.0) + (father.initial_sugar / 2.0)
            mother.sugar -= mother.initial_sugar / 2.0
            father.sugar -= father.initial_sugar / 2.0

            args["spice"] = (mother.initial_spice / 2.0) + (father.initial_spice / 2.0)
            mother.spice -= mother.initial_spice / 2.0
            father.spice -= father.initial_spice / 2.0

            # create the child's initial cultural tags
            num_tags = len(self.culture_tags) #TODO account for different length tags?
            child_tags = []
            for i in range(0, num_tags):
                if mother.culture_tags[i] == father.culture_tags[i]:
                    child_tags.append(mother.culture_tags[i])
                else:
                    child_tags.append(self.rand.choice((0, 1)))

            args["culture_type"] = self.rand.choice((mother.culture_type, father.culture_type))
            args["culture_tags"] = child_tags

            # create the child's immune system
            I = []
            IM = mother.initial_immune_sys
            IF = father.initial_immune_sys
            for i in range(len(IM)):
                if IM[i] == IF[i]:
                    I.append(IM[i])
                else:
                    I.append(self.rand.choice((0, 1)))

            args["immune_sys"] = I

            # spawn the child in the world
            child = self.world.spawnAgent(args)

            # update family connections
            mother.children.append(child)
            father.children.append(child)
            mother.mates.append(father)
            father.mates.append(mother)


    def isFertile(self):
        return (self.fertile_age_start <= self.age <= self.fertile_age_end
            and self.sugar >= self.initial_sugar
            and self.spice >= self.initial_spice)


    def isSuitableMate(self, a):
        if a is None:
            return False

        if not a.isFertile():
            return False

        if a.gender == self.gender:
            return False

        return True
        

    def immuneResponse(self):
        if not self.diseases:
            return

        d = self.diseases[0]

        # if the disease has not had an immune response yet, position will be None.
        # we must find the substring in immume_sys that has the closest hamming
        # distance to the diseases's string
        if d.position is None:
            I = self.immune_sys
            D = d.string
            min_dist, position = len(D), 0

            for i in range(len(I) - len(D)):
                dist = 0
                for bit2 in D:
                    if I[i] != bit2:
                        dist += 1

                if dist < min_dist:
                    min_dist = dist
                    position = i
            d.position = position


        # fight the disease
        I = self.immune_sys
        D = d.string
        p = d.position
        for i in range(len(D)):
            if I[p+i] != D[i]:
                I[p+i] = D[i]
                break;

        # check if flipping the bit cured the disease
        d.cured = True
        for i in range(len(D)):
            if I[p+i] != D[i]:
                d.cured = False
                break;

        self.diseases = [d for d in self.diseases if not d.cured]


    def infect(self, d):
        for d2 in self.diseases:
            if d.string == d2.string:
                return

        # check if the agent is currently immune
        I = self.immune_sys
        D = d.string

        for i in range(len(I) - len(D)):
            dist = 0
            for bit2 in D:
                if I[i] != bit2:
                    dist += 1

            if dist == 0:
                return;

        # FIXME don't really need to copy but simplifies implementaion
        disease = copy.deepcopy(d)
        disease.position = None
        disease.cured = False
        self.diseases.append(disease)


    def infectNeighbours(self):
        if not self.diseases:
            return

        ns = self.world.getNeighbourAgents(self.x, self.y)
        for n in ns:
            n.infect(self.rand.choice(self.diseases))

