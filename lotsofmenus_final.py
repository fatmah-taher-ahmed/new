from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup_final import Category, Base, Item
 
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()



#catecories 1
Snowboarding = Category(cname = "Snowboarding")
session.add(Snowboarding)
session.commit()

Goggle = Item(iname = "Goggle", description = """ snowboard goggle selection at The House Outdoor gear offers a huge variety of the best snowboard goggles""",  category = Snowboarding)
session.add(Goggle)
session.commit()
Snowboard = Item(iname = "Snowboard", description = """is a recreational activity and Winter Olympicand Paralympic sport """,  category = Snowboarding)
session.add(Snowboard)
session.commit()

#categories 2
Soccer = Category(cname = "Soccer")
session.add(Soccer)
session.commit()

Two_shinguards = Item(iname = "Two shinguards", description = """A shin guard or shin pad or canilleras""",  category = Soccer)
session.add(Two_shinguards)
session.commit()

Shinguards = Item(iname = "Shinguards", description = """A shin guard or shin pad or canilleras,is a piece of equipment worn on the front of a player's shin to protect it from injury. """,  category = Soccer)
session.add(Shinguards)
session.commit()

Jersey = Item(iname = "Jersey", description = """Jersey City was an American soccer club basedin Jersey City""",  category = Soccer)
session.add(Jersey)
session.commit()

Soccer_cleats = Item(iname = "Soccer cleats", description = """Cleats or studs are protrusions on the sole of a shoe""",  category = Soccer)
session.add(Soccer_cleats)
session.commit()


#categories 3
Frisbee = Category(cname = "Frisbee")
session.add(Frisbee)
session.commit()

Frisbee1 = Item(iname = "Frisbee", description = """called a flying disc or simply a disc is a gliding toy or sporting item, It is used recreationally and competitively for throwing and catching""",  category = Frisbee)
session.add(Frisbee1)
session.commit()

#categories 4
Hockey = Category(cname = "Hockey")
session.add(Hockey)
session.commit()

Stick = Item(iname = "Stick", description = """ is a piece of sport equipment used by the players in all the forms of hockey to move the ball """,  category = Hockey)
session.add(Stick)
session.commit()

# categories 5
Baseball = Category(cname = "Baseball")
session.add(Baseball)
session.commit()

Bat = Item(iname = "Bat", description = """A baseball bat is a smooth wooden or """,  category = Baseball)
session.add(Bat)
session.commit()

# categories 6
Skating = Category(cname = "Skating")
session.add(Skating)
session.commit()

#categories 7
Foosball = Category(cname = "Foosball")
session.add(Foosball)
session.commit()

# categories 8
Rockcliming = Category(cname = "Rockcliming")
session.add(Rockcliming)
session.commit()

# categories 9
Basketball = Category(cname = "Basketball")
session.add(Basketball)
session.commit()


print ("added item !")
