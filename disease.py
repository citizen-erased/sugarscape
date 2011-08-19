class Disease():
    def __init__(self, rand, length, extra_sugar, extra_spice):
        self.extra_sugar = extra_sugar
        self.extra_spice = extra_spice
        self.string = []

        for i in range(length):
            self.string.append(rand.choice((1, 0)))

