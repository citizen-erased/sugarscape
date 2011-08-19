import sys, os, yaml, util

from random import Random
from PySFML import sf
from OpenGL.GL import *
from camera import Camera
from agent import Agent
from disease import Disease
from statistics import Statistics
from data_vis import DataVis


#---------------------------------------------------------------------------#
#                                                                           #
#                         Sugarscape Simulation                             #
#                                                                           #
#---------------------------------------------------------------------------#
class Sugarscape():

#---------------------------------------------------------------------------#
#                                Tile Data                                  #
#---------------------------------------------------------------------------#
    class Tile():
        def __init__(self, sugar, spice):
            self.sugar = float(sugar)
            self.spice = float(spice)
            
            self.max_sugar = self.sugar
            self.max_spice = self.spice

            self.pollution = 0.0

            self.agent = None
            self.region = None


    class Season():
        # Seasons is an array of dictionaries where each dictionary where each
        # dictionary defines a season. A season defines growth rates for a 
        # number of ticks. Each dictionary should contain:
        # ["ticks"] the number of ticks for the rates to be active
        # ["sugar_growth"] the sugar growth
        # ["spice_growth"] the spice growth
        #
        # When a season has been active for its defined number of ticks, the
        # current season is set to the next season in the array, wrapping back
        # to the start if necessary.
        def __init__(self, ticks, sugar_growth, spice_growth):
            self.ticks = ticks
            self.sugar_growth = sugar_growth
            self.spice_growth = spice_growth


    class Region():
        # x1, y1, x2, y2 specify a rectangular region of tiles that make up the
        # region.
        #
        # Tiles are inclusive.
        # x1 < x2 and y1 < y2
        #
        # seasons is an array of Seasons. Initially the current_season is set to
        # the first Season in the array.
        # When a season has been active for its defined number of ticks, the
        # current season is set to the next season in the array, wrapping back
        # to the start if necessary.
        def __init__(self, seasons):
            #self.x1, self.y1 = x1, y1
            #self.x2, self.y2 = x2, y2

            if seasons:
                self.seasons = seasons
            else:
                self.seasons = [Sugarscape.Season(1000, 1, 1)]

            self.time = 0
            self.current_index = 0
            self.current_season = self.seasons[0]


        def tick(self):
            if self.time >= self.current_season.ticks:
                self.time = 0
                self.current_index += 1

                if self.current_index >= len(self.seasons):
                    self.current_index = 0

                self.current_season = self.seasons[self.current_index]

            self.time += 1





#---------------------------------------------------------------------------#
#                                                                           #
#                            initialization/shutdown                        #
#                                                                           #
#---------------------------------------------------------------------------#
    def __init__(self):
        self.window = sf.RenderWindow()


    def init(self):
        self.rand = Random()

        # tilemap
        self.loadData("sugarscape.yaml")
        data = self.data_file

        # agent properties
        self.num_agents             = data["num_agents"]
        self.vision_range           = data["vision_range"]
        self.sugar_metabolism_range = data["sugar_metabolism_range"]
        self.spice_metabolism_range = data["spice_metabolism_range"]
        self.initial_sugar_range    = data["initial_sugar_range"]
        self.initial_spice_range    = data["initial_spice_range"]
        self.max_age_range          = data["max_age_range"]
        self.m_fertile_start_range  = data["m_fertile_start_range"]
        self.m_fertile_end_range    = data["m_fertile_end_range"]
        self.f_fertile_start_range  = data["f_fertile_start_range"]
        self.f_fertile_end_range    = data["f_fertile_end_range"]
        self.num_culture_tags       = data["num_culture_tags"]

        # agent mutations
        self.vision_mutation_chance           = data["vision_mutation_chance"]
        self.global_vision_range              = data["global_vision_range"]
        self.vision_mutation_range            = data["vision_mutation_range"]

        self.sugar_metabolism_mutation_chance = data["sugar_metabolism_mutation_chance"]
        self.global_sugar_metabolism_range    = data["global_sugar_metabolism_range"]
        self.sugar_metabolism_mutation_range  = data["sugar_metabolism_mutation_range"]

        self.spice_metabolism_mutation_chance = data["spice_metabolism_mutation_chance"]
        self.global_spice_metabolism_range    = data["global_spice_metabolism_range"]
        self.spice_metabolism_mutation_range  = data["spice_metabolism_mutation_range"]

        self.age_mutation_chance              = data["age_mutation_chance"]
        self.global_age_range                 = data["global_age_range"]
        self.age_mutation_range               = data["age_mutation_range"]

        # pollution properties
        self.pollution_ticks            = data["pollution_ticks"]
        self.pollution_sugar_metabolism = data["pollution_sugar_metabolism"]
        self.pollution_spice_metabolism = data["pollution_spice_metabolism"]
        self.pollution_harvest          = data["pollution_harvest"]
        self.pollution_decay            = data["pollution_decay"]

        # diseases
        self.diseases = []
        self.num_initial_diseases        = data["num_initial_diseases"]
        self.disease_string_length_range = data["disease_string_length_range"]
        self.disease_extra_sugar_range   = data["disease_extra_sugar_range"]
        self.disease_extra_spice_range   = data["disease_extra_spice_range"]

        self.disease_infliction_ticks     = data["disease_infliction_ticks"]
        self.disease_infliction_agents    = data["disease_infliction_agents"]
        self.next_disease_infliction_tick = self.disease_infliction_ticks

        for i in range(self.num_initial_diseases):
            d = Disease(self.rand,
                self.rand.randint(self.disease_string_length_range[0], self.disease_string_length_range[1]),
                self.rand.randint(self.disease_extra_sugar_range[0], self.disease_extra_sugar_range[1]),
                self.rand.randint(self.disease_extra_spice_range[0], self.disease_extra_spice_range[1]))
            self.diseases.append(d)

        # simulation variables
        self.current_tick = 0
        self.next_pollution_tick = self.pollution_ticks - 1
        self.num_births = 0
        self.num_deaths = 0
        self.death_causes = {}
        self.paused = False

        # agents
        self.agents = []
        for i in range(min(self.tiles_x * self.tiles_y, self.num_agents)):
            args = {
                "sugar_metabolism"  : self.rand.randint(self.sugar_metabolism_range[0], self.sugar_metabolism_range[1]),
                "spice_metabolism"  : self.rand.randint(self.spice_metabolism_range[0], self.spice_metabolism_range[1]),
                "vision"            : self.rand.randint(self.vision_range[0], self.vision_range[1]),
                "sugar"             : self.rand.randint(self.initial_sugar_range[0], self.initial_sugar_range[1]),
                "spice"             : self.rand.randint(self.initial_spice_range[0], self.initial_spice_range[1]),
                "max_age"           : self.rand.randint(self.max_age_range[0], self.max_age_range[1]),
                "gender"            : self.rand.choice(("male", "female")),
            }

            if args["gender"] == "male":
                fertile_start_range = self.m_fertile_start_range
                fertile_end_range   = self.m_fertile_end_range
            else:
                fertile_start_range = self.f_fertile_start_range
                fertile_end_range   = self.f_fertile_end_range

            args["fertile_age_start"] = self.rand.randint(fertile_start_range[0], fertile_start_range[1])
            args["fertile_age_end"] = self.rand.randint(fertile_end_range[0], fertile_end_range[1])

            args["culture_tags"] = [self.rand.choice((0, 1)) for _ in range(0, self.num_culture_tags)]
            args["culture"] = "BasicCulture"

            self.rand.shuffle(self.diseases)
            args["diseases"] = self.diseases[:data["num_agent_diseases"]]
            args["immune_sys"] = [self.rand.choice((0, 1)) for _ in range(0, 50)]

            # find an unoccupied tile
            location_taken = True
            while location_taken:
                x = self.rand.randint(0, self.tiles_x-1)
                y = self.rand.randint(0, self.tiles_y-1)
                location_taken = self.isTileOccupied(x, y)

            args["x"], args["y"] = x, y

            self.spawnAgent(args)

        # rendering
        self.window.Create(sf.VideoMode(800, 600), "sugarscape")
        self.window.SetActive(True)
        self.window.PreserveOpenGLStates(True)
        self.window.SetFramerateLimit(60)
        self.cam = Camera(0, 0, 800, 600)
        self.resized(800, 600)
        self.resetCamera()
        glDisable(GL_DEPTH_TEST)

        self.tile_size = 10
        self.agent_size = 6

        self.draw_tiles_func = self.drawSugarTiles
        self.draw_agents_func = self.drawAgentsGender

        # statistics
        self.stats = Statistics(self)
        self.data_vis = DataVis(self.stats)

        # Gather stats for the initial simulation state (tick 0).
        # Do this here since the simulation is ticked, then stats are gathered
        # for it and displayed.
        self.stats.tick()


    def deinit(self):
        self.window.Close()


#---------------------------------------------------------------------------#
#                                                                           #
#                               main loop/ticking                           #
#                                                                           #
#---------------------------------------------------------------------------#
    def run(self):
        self.init()
        self.running = True

        while self.running:
            self.doEvents()

            if not self.paused:
                self.tick()
                self.stats.tick()
                self.data_vis.tick()

            self.draw()
            self.data_vis.draw()

        self.deinit()


    def doEvents(self):
        event = sf.Event()
        while self.window.GetEvent(event):
            if event.Type in [sf.Event.KeyPressed, sf.Event.KeyReleased]:
                self.keyEvent(event)
            elif event.Type == sf.Event.Closed:
                self.running = False
            elif event.Type == sf.Event.Resized:
                self.resized(event.Size.Width, event.Size.Height)

    
#---------------------------------------------------------------------------#
#                               input events                                #
#---------------------------------------------------------------------------#
    def keyEvent(self, evt):
        c = evt.Key.Code
        shift, ctrl, alt = evt.Key.Shift, evt.Key.Control, evt.Key.Alt

        if evt.Type == sf.Event.KeyPressed:
            if c == sf.Key.V:
                self.data_vis.setRunning(not self.data_vis.running)
            elif c == sf.Key.Space:
                self.paused = not self.paused
            elif c == sf.Key.Escape:
                self.running = False

            # tile drawing modes
            elif c == sf.Key.Q:
                print "draw sugar"
                self.draw_tiles_func = self.drawSugarTiles
            elif c == sf.Key.W:
                print "draw spice"
                self.draw_tiles_func = self.drawSpiceTiles
            elif c == sf.Key.E:
                print "draw occupied"
                self.draw_tiles_func = self.drawOccupiedTiles
            elif c == sf.Key.R:
                print "draw pollution"
                self.draw_tiles_func = self.drawPollution

            # agent drawing modes
            elif c == sf.Key.Num1:
                print "draw agents"
                self.draw_agents_func = self.drawAgents
            elif c == sf.Key.Num2:
                print "draw agents gender"
                self.draw_agents_func = self.drawAgentsGender
            elif c == sf.Key.Num3:
                print "draw agents culture"
                self.draw_agents_func = self.drawAgentsCulture
            elif c == sf.Key.Num4:
                print "draw agents sugar"
                self.draw_agents_func = self.drawAgentsSugar
            elif c == sf.Key.Num5:
                print "draw agents spice"
                self.draw_agents_func = self.drawAgentsSpice
            elif c == sf.Key.Num6:
                print "draw agents health"
                self.draw_agents_func = self.drawAgentsHealth

            elif c == sf.Key.F1:
                img = self.window.Capture()
                num = 0
                name = "screenshots/" + str(num).zfill(6) + ".png"
                while os.path.exists(name):
                    num = num + 1
                    name = "screenshots/" + str(num).zfill(6) + ".png"
                print "saving screenshot '{0}'".format(name)
                img.SaveToFile(name)

                if(self.data_vis.running):
                    img = self.data_vis.window.Capture()
                    name = "screenshots/" + str(num).zfill(6) + "_data.png"
                    img.SaveToFile(name)



#---------------------------------------------------------------------------#
#                                   ticking                                 #
#---------------------------------------------------------------------------#
    def tick(self):
        self.num_births = 0
        self.num_deaths = 0
        self.death_causes.clear()

        for r in self.regions.itervalues():
            r.tick()

        self.growResourcesRegional()

        if self.next_pollution_tick <= self.current_tick:
            self.pollutionDecay()
            self.pollutionDiffusion()
            self.next_pollution_tick = self.current_tick + self.pollution_ticks

        if self.current_tick >= self.next_disease_infliction_tick:
            self.inflictDiseaseOnAgents()

        for a in self.agents:
            a.tick()

            if a.dead:
                self.setAgentAt(None, a.x, a.y)
                self.num_deaths += 1
                self.death_causes.setdefault(a.death_cause, 0)
                self.death_causes[a.death_cause] += 1
         
        self.agents = [a for a in self.agents if not a.dead]
        self.rand.shuffle(self.agents)

        self.current_tick += 1

        #print "births={0} deaths={1}".format(self.num_births, self.num_deaths)
        if self.death_causes:
            print self.death_causes

        
#---------------------------------------------------------------------------#
#                                                                           #
#                           Tilemap functions                               #
#                                                                           #
#---------------------------------------------------------------------------#
    def loadData(self, data_file_path):
        self.data_file = yaml.load(file(data_file_path, 'r'))

        if "random_seed" in self.data_file:
            seed = self.data_file["random_seed"]
        else:
            seed = self.rand.randint(0, sys.maxint)

        print "seeding RNG with {0}".format(seed)
        self.rand.seed(seed)

        sugar_img, spice_img, region_img = sf.Image(), sf.Image(), sf.Image()
        sugar_img.LoadFromFile(self.data_file["sugar_file"])
        spice_img.LoadFromFile(self.data_file["spice_file"])
        region_img.LoadFromFile(self.data_file["regions_file"])

        self.tiles_x = sugar_img.GetWidth()
        self.tiles_y = spice_img.GetHeight()

        self.tiles = []
        self.max_sugar_level = 1.0
        self.max_spice_level = 1.0

        for x in range(self.tiles_x):
            self.tiles.append([])
            for y in range(self.tiles_y):
                c_sugar = sugar_img.GetPixel(x, sugar_img.GetHeight()-y-1)
                c_spice = spice_img.GetPixel(x, spice_img.GetHeight()-y-1)
                t = Sugarscape.Tile(c_sugar.r, c_spice.r)
                self.tiles[x].append(t)
                self.max_sugar_level = float(max(self.max_sugar_level, t.max_sugar))
                self.max_spice_level = float(max(self.max_spice_level, t.max_spice))

        #s1 = Sugarscape.Season(50, 1.0, 1.0)
        #s2 = Sugarscape.Season(50, 1.0, 1.0)
        #r1 = Sugarscape.Region(0,0,self.tiles_x-1,(self.tiles_y-1)/2, [s1, s2])
        #r2 = Sugarscape.Region(0,(self.tiles_y-1)/2,self.tiles_x-1,self.tiles_y-1, [s2, s1])
        #self.regions = []
        #self.regions.append(r1)
        #self.regions.append(r2)

        #for r in self.regions:
        #    for x in range(r.x1, r.x2+1):
        #        for y in range(r.y1, r.y2+1):
        #            self.tiles[x][y].region = r

        seasons = {}
        for s_data in self.data_file["seasons"]:
            seasons[s_data["name"]] = Sugarscape.Season(s_data["ticks"], s_data["sugar_growth"], s_data["spice_growth"])

        self.regions = {}
        for r_data in self.data_file["regions"]:
            S = []
            for s_name in r_data["season_names"]:
                if s_name in seasons:
                    S.append(seasons[s_name])

            if not S:
                print "region {0} has no associated seasons!".format(r_data["region_id"])

            self.regions[r_data["region_id"]] = Sugarscape.Region(S)

        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                r_id = region_img.GetPixel(x, region_img.GetHeight()-y-1).r
                if r_id in self.regions:
                    self.tiles[x][y].region = self.regions[r_id]
                else:
                    print "tile[{0}][{1}] has no associated region!".format(x, y)


    def growResourcesGlobal(self, growth):
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                t = self.tiles[x][y]
                t.sugar = min(t.sugar + growth, t.max_sugar)
                t.spice = min(t.spice + growth, t.max_spice)


    def growResourcesRegional(self):
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                t = self.tiles[x][y]
                g_sugar = t.region.current_season.sugar_growth
                g_spice = t.region.current_season.spice_growth
                t.sugar = min(t.sugar + g_sugar, t.max_sugar)
                t.spice = min(t.spice + g_spice, t.max_spice)
        

    def pollutionDiffusion(self):
        averages = util.create2DArray(self.tiles_x, self.tiles_y, 0.0)
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                avg  = self.getTileAt(x-1, y).pollution
                avg += self.getTileAt(x+1, y).pollution
                avg += self.getTileAt(x, y-1).pollution
                avg += self.getTileAt(x, y+1).pollution
                averages[x][y] = avg / 4.0

        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                self.getTileAt(x, y).pollution = averages[x][y]


    def pollutionDecay(self):
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                p = self.tiles[x][y].pollution
                self.tiles[x][y].pollution = max(p - self.pollution_decay, 0)


    def harvestSugarAt(self, x, y):
        t = self.getTileAt(x, y)
        s = t.sugar
        t.sugar = 0
        self.addPollution(x, y, self.pollution_harvest * s)
        return s


    def harvestSpiceAt(self, x, y):
        t = self.getTileAt(x, y)
        s = t.spice
        t.spice = 0
        self.addPollution(x, y, self.pollution_harvest * s)
        return s


    def getTileAt(self, x, y):
        return self.tiles[x % self.tiles_x][y % self.tiles_y]


    def getSugarAt(self, x, y):
        return self.getTileAt(x, y).sugar


    def getSpiceAt(self, x, y):
        return self.getTileAt(x, y).spice


    def getPollutionAt(self, x, y):
        return self.getTileAt(x, y).pollution


    def addPollution(self, x, y, amount):
        self.getTileAt(x, y).pollution += amount


    def addSugarMetabolismPollution(self, x, y, sugar):
        self.addPollution(x, y, self.pollution_sugar_metabolism * sugar)

    
    def addSpiceMetabolismPollution(self, x, y, spice):
        self.addPollution(x, y, self.pollution_spice_metabolism * spice)

    
    def spawnAgent(self, args):
        a = Agent(self, **args)
        self.agents.append(a)
        self.setAgentAt(a, a.x, a.y)
        self.num_births += 1
        return a


    def setAgentAt(self, agent, x, y):
        self.getTileAt(x, y).agent = agent
        return x % self.tiles_x, y % self.tiles_y


    def getAgentAt(self, x, y):
        return self.getTileAt(x, y).agent


    def getNeighbourAgents(self, x, y):
        ns = [
            self.getAgentAt(x-1, y),
            self.getAgentAt(x+1, y),
            self.getAgentAt(x, y-1),
            self.getAgentAt(x, y+1),
        ]

        return [a for a in ns if a is not None]

        
    def updateAgentPosition(self, agent, old_x, old_y, new_x, new_y):
        self.setAgentAt(None, old_x, old_y)
        return self.setAgentAt(agent, new_x, new_y)


    def isTileOccupied(self, x, y):
        return self.getAgentAt(x, y) is not None


    def tileHasEmptyNeighbour(self, x, y):
        return (self.getAgentAt(x-1, y) is None
             or self.getAgentAt(x+1, y) is None
             or self.getAgentAt(x, y-1) is None
             or self.getAgentAt(x, y+1) is None)


    def getEmptyNeighbourTiles(self, x, y):
        n_locs = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
        return [l for l in n_locs if not self.isTileOccupied(l[0], l[1])]


    def getWorldSize(self):
        return self.tiles_x, self.tiles_y

    

#---------------------------------------------------------------------------#
#                                                                           #
#                           Agent functions                                 #
#                                                                           #
#---------------------------------------------------------------------------#
    def getNumAgents(self):
        return len(self.agents)


    def inflictDiseaseOnAgents(self):
        self.next_disease_infliction_tick = self.current_tick + self.disease_infliction_ticks

        if not self.agents:
            return

        for i in range(self.disease_infliction_agents):
            a = self.rand.choice(self.agents)
            d = self.rand.choice(self.diseases)
            a.infect(d)
        

#---------------------------------------------------------------------------#
#                                                                           #
#                            drawing/window functions                       #
#                                                                           #
#---------------------------------------------------------------------------#
    def draw(self):
        self.window.SetActive(True)
        glLoadIdentity()
        glClear(GL_COLOR_BUFFER_BIT)

        # center the world if smaller than the screen
        win_w, win_h = self.window.GetWidth(), self.window.GetHeight()
        world_w, world_h = self.getWorldSize()
        world_w *= self.tile_size
        world_h *= self.tile_size

        if world_w < win_w:
            glTranslatef((win_w - world_w) / 2, 0.0, 0.0)
        if world_h < win_h:
            glTranslatef(0.0, (win_h - world_h) / 2, 0.0)

        # apply camera transform
        glTranslatef(-self.cam.x, -self.cam.y, 0.0)

        # draw the world
        self.draw_tiles_func()
        self.draw_agents_func()

        # swap buffers
        self.window.Display()
        #print self.window.GetFrameTime()


    def drawSugarTiles(self):
        s = self.tile_size
        glBegin(GL_QUADS)
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                t = self.tiles[x][y]
                glColor3f(t.sugar/self.max_sugar_level, t.sugar/self.max_sugar_level, 0.0)
                glVertex2f(x*s,     y*s)
                glVertex2f((x+1)*s, y*s)
                glVertex2f((x+1)*s, (y+1)*s)
                glVertex2f(x*s,     (y+1)*s)
        glEnd()


    def drawSpiceTiles(self):
        s = self.tile_size
        glBegin(GL_QUADS)
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                t = self.tiles[x][y]
                glColor3f(t.spice/self.max_spice_level, t.spice/self.max_spice_level, 0.0)
                glVertex2f(x*s,     y*s)
                glVertex2f((x+1)*s, y*s)
                glVertex2f((x+1)*s, (y+1)*s)
                glVertex2f(x*s,     (y+1)*s)
        glEnd()


    def drawOccupiedTiles(self):
        s = self.tile_size
        glColor3ub(255, 0, 0)
        glBegin(GL_QUADS)
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                t = self.tiles[x][y]
                if self.isTileOccupied(x, y):
                    glVertex2f(x*s,     y*s)
                    glVertex2f((x+1)*s, y*s)
                    glVertex2f((x+1)*s, (y+1)*s)
                    glVertex2f(x*s,     (y+1)*s)
        glEnd()


    def drawPollution(self):
        s = self.tile_size
        glBegin(GL_QUADS)
        for x in range(self.tiles_x):
            for y in range(self.tiles_y):
                t = self.tiles[x][y]
                c = t.pollution/255.0
                glColor3f(c,c,c)
                glVertex2f(x*s,     y*s)
                glVertex2f((x+1)*s, y*s)
                glVertex2f((x+1)*s, (y+1)*s)
                glVertex2f(x*s,     (y+1)*s)
        glEnd()
    

    def drawAgents(self):
        t_s = self.tile_size
        a_s = self.agent_size
        off = (t_s - a_s) / 2

        glBegin(GL_QUADS)
        for a in self.agents:
            glColor3ub(0, 0, 255)
            x,y = a.x*t_s+off, a.y*t_s+off
            glVertex2f(x,     y)
            glVertex2f(x+a_s, y)
            glVertex2f(x+a_s, y+a_s)
            glVertex2f(x,     y+a_s)
        glEnd()


    def drawAgentsGender(self):
        t_s = self.tile_size
        a_s = self.agent_size
        off = (t_s - a_s) / 2

        glBegin(GL_QUADS)
        for a in self.agents:
            if a.gender == "male":
                glColor3ub(24, 116, 205)
            else:
                glColor3ub(255, 20, 147)
            x,y = a.x*t_s+off, a.y*t_s+off
            glVertex2f(x,     y)
            glVertex2f(x+a_s, y)
            glVertex2f(x+a_s, y+a_s)
            glVertex2f(x,     y+a_s)
        glEnd()


    def drawAgentsCulture(self):
        t_s = self.tile_size
        a_s = self.agent_size
        off = (t_s - a_s) / 2

        glBegin(GL_QUADS)
        for a in self.agents:
            cul = a.culture.getGroup()
            col = a.culture.COLORS.get(cul, (1.0, 1.0, 1.0, 1.0))
            glColor4f(col[0], col[1], col[2], col[3])

            x,y = a.x*t_s+off, a.y*t_s+off
            glVertex2f(x,     y)
            glVertex2f(x+a_s, y)
            glVertex2f(x+a_s, y+a_s)
            glVertex2f(x,     y+a_s)
        glEnd()


    def drawAgentsSugar(self):
        t_s = self.tile_size
        a_s = self.agent_size
        off = (t_s - a_s) / 2

        glBegin(GL_QUADS)
        for a in self.agents:
            max_s = 100.0
            s = max(min(a.sugar, max_s), 0.0)
            s /= max_s
            r, g = (1.0 - s), s

            glColor4f(r, g, 0.0, 1.0)

            x,y = a.x*t_s+off, a.y*t_s+off
            glVertex2f(x,     y)
            glVertex2f(x+a_s, y)
            glVertex2f(x+a_s, y+a_s)
            glVertex2f(x,     y+a_s)
        glEnd()


    def drawAgentsSpice(self):
        t_s = self.tile_size
        a_s = self.agent_size
        off = (t_s - a_s) / 2

        glBegin(GL_QUADS)
        for a in self.agents:
            max_s = 100.0
            s = max(min(a.spice, max_s), 0.0)
            s /= max_s
            r, g = (1.0 - s), s

            glColor4f(r, g, 0.0, 1.0)

            x,y = a.x*t_s+off, a.y*t_s+off
            glVertex2f(x,     y)
            glVertex2f(x+a_s, y)
            glVertex2f(x+a_s, y+a_s)
            glVertex2f(x,     y+a_s)
        glEnd()


    def drawAgentsHealth(self):
        t_s = self.tile_size
        a_s = self.agent_size
        off = (t_s - a_s) / 2

        glBegin(GL_QUADS)
        for a in self.agents:
            if a.diseases:
                glColor4f(1.0, 0.0, 0.0, 1.0)
            else:
                glColor4f(0.0, 1.0, 0.0, 1.0)

            x,y = a.x*t_s+off, a.y*t_s+off
            glVertex2f(x,     y)
            glVertex2f(x+a_s, y)
            glVertex2f(x+a_s, y+a_s)
            glVertex2f(x,     y+a_s)
        glEnd()


    def resetCamera(self):
        win_w, win_h = self.window.GetWidth(), self.window.GetHeight()
        world_w, world_h = self.getWorldSize()
        self.cam.width = min(win_w, world_w)
        self.cam.height = min(win_h, world_h)


    def resized(self, width, height):
        self.window.SetView(sf.View(sf.FloatRect(0, 0, width, height)))

        self.window.SetActive(True)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_MODELVIEW)

