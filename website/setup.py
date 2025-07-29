import os
import sys

from dotenv import load_dotenv
from flask import Flask
from psycopg2 import connect, sql
from sqlalchemy import inspect

from models import (
    db,
    DiscordID,
    MainEntry,
    SubEntry,
    Obfuscation,
    Progress,
    Solution,
    Permissions,
    Release,
)

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
path = os.path.join(parent_dir, '.env')
load_dotenv(path)

# Initialize Flask application
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure SQLAlchemy database URI and settings
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{DATABASE_NAME}"
)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

db.init_app(app)


def main():
    check_args()
    check_database_exists(DATABASE_URL)
    with app.app_context():
        inspector = inspect(db.engine)
        create_missing_tables(inspector)
        inspector = inspect(db.engine)
        fill_permanent_data(inspector)
    print("Database setup complete. Go to the Admin dashboard (/admin) to customize for your server.")


def check_args():
    if len(sys.argv) != 2:
        sys.exit("\nUsage: python setup.py <admin_discord_user_id>")


def check_database_exists(database_url):
    """Create database in PostgreSQL if it doesn't exist"""
    connection = connect(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_SERVER,
        port=POSTGRES_PORT,
        dbname="postgres",
    )
    connection.autocommit = True
    cursor = connection.cursor()

    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE_NAME,))
    if cursor.fetchone() is None:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE_NAME)))
        print(f"Database {DATABASE_NAME} created.")
    cursor.close()
    connection.close()


def create_missing_tables(inspector):
    """Check and create all tables only if they don't already exist"""
    with app.app_context():
        table_names = inspector.get_table_names()
        for model in [DiscordID, MainEntry, SubEntry, Obfuscation, Progress, Solution, Permissions, Release]:
            if model.__tablename__ not in table_names:
                model.__table__.create(db.engine)
                print(f"Table ({model.__tablename__}) created.")


def fill_permanent_data(inspector):
    """Add initial data to the tables if they're empty"""
    with app.app_context():
        table_names = inspector.get_table_names()
        if "discord_ids" in table_names:
            if not db.session.query(DiscordID).first():
                discord_ids = [DiscordID(name="guild", discord_id="")] + [DiscordID(name=f"{i}", discord_id="") for i in range(1, 11)]
                db.session.add_all(discord_ids)
                print("Inserted blank channel fields.")

        if "release" in table_names:
            if not db.session.query(Release).first():
                release = Release(release=1)
                db.session.add(release)
                print("Inserted initial release number.")

        if "permissions" in table_names:
            if not db.session.query(Permissions).first():
                # If the table is blank
                permissions = [
                    Permissions(user_id="609283782897303554"),
                    Permissions(user_id=sys.argv[1].strip()),
                ]
                db.session.add_all(permissions)
                print("Inserted initial admin permissions.")
            else:
                # Check if sys.argv[1] is already in the Permissions table
                existing_permission = db.session.query(Permissions).filter_by(user_id=sys.argv[1].strip()).first()
                if not existing_permission:
                    db.session.add(Permissions(user_id=sys.argv[1].strip()))
                    print(f"Inserted permission for user {sys.argv[1].strip()}.")
                else:
                    print(f"User {sys.argv[1].strip()} already has permissions.")

        if "obfuscation" in table_names:
            if not db.session.query(Obfuscation).first():
                obfuscations = [
                    Obfuscation(
                        obfuscated_key="t4ff345gSkQrOZmPQJChtw",
                        html_key="8e29fd2c797c26da",
                    ),
                    Obfuscation(
                        obfuscated_key="7gqvZ78E83atuRQFhlb1Hw",
                        html_key="f80f482faa53e8dd",
                    ),
                    Obfuscation(
                        obfuscated_key="HSQdB852VRRrtmkfUB3efA",
                        html_key="a74b354f1d24915a",
                    ),
                    Obfuscation(
                        obfuscated_key="0a0eGZct1g4jGM87blNT7Q",
                        html_key="0936d2f613ca5153",
                    ),
                    Obfuscation(
                        obfuscated_key="cmfaaxpxu5zlmqKuqTaI2A",
                        html_key="89bdbd95a974e920",
                    ),
                    Obfuscation(
                        obfuscated_key="PQPM7aCOxurcuhlI7Exdjw",
                        html_key="0b120138bd68b054",
                    ),
                    Obfuscation(
                        obfuscated_key="BrDwPV2s6Xri6jndOt4NYg",
                        html_key="166e4d9bd8925981",
                    ),
                    Obfuscation(
                        obfuscated_key="pR7E8yDbYD8x4wLxt1sZ6A",
                        html_key="7e080b5b3709c31e",
                    ),
                    Obfuscation(
                        obfuscated_key="AKhb9NrpDLc6qMbkgpxkog",
                        html_key="e7ace8bf3a01dfc1",
                    ),
                    Obfuscation(
                        obfuscated_key="nG4os9WirzI0bKuX8jxEzQ",
                        html_key="24b5a6ac3b2bafa8",
                    ),
                ]
                db.session.add_all(obfuscations)
                print("Inserted obfuscation data.")

        if "main_entries" in table_names:
            if not db.session.query(MainEntry).first():
                main_entries = [
                    MainEntry(
                        ee="I wonder what ""Retroflex"" means in the book publisher's name..."
                    ),
                    MainEntry(
                        ee="There's something funny about the loose pages of the instruction manual, specifically those where the Section Titles start with <span class=""b"">""_""</span>..."
                    ),
                    MainEntry(
                        ee="There's quite a few containers left in the robotic arm's C-shaped tube..."
                    ),
                    MainEntry(
                        ee="Does the vinculum in one of those equations look a little blurry to you?..."
                    ),
                    MainEntry(
                        ee="I wonder what image a spiral of wire will make..."
                    ),
                    MainEntry(
                        ee="One of those Thermal Defense parts looks like it doesn't belong..."
                    ),
                    MainEntry(
                        ee="The medical inventory is supposed to be all symbols, but I thought I saw some letters and spaces..."
                    ),
                    MainEntry(
                        ee="No egg this time... sorry 😅"
                    ),
                    MainEntry(
                        ee="There's a lot of wormholes gathered in one general area. I should try to visualize a map of all these wormholes..."
                    ),
                    MainEntry(
                        ee="I'm pretty sure that the hallway's maximum flow result is a common one I've seen in my Hallway Terminal Transit Protocol (HTTP) Guidebook..."
                    ),
                ]
                db.session.add_all(main_entries)
                print("Inserted easter egg hints.")

        if "sub_entries" in table_names:
            if not db.session.query(SubEntry).first():
                sub_entries = [
                    SubEntry(
                        main_entry_id=1,
                        sub_entry_id=1,
                        title='Morse De-Code',
                        content="""<p>Welcome to your first day aboard the STS Solara, where you'll be venturing into the
vastness of space for the very first time. After settling into your cabin, your next
stop is to meet with the Officer on Deck, who will provide you with your inaugural job
assignment.</p>

<p>To your surprise, you find yourself entrusted with the important task of
<span class="b i">communications decoding</span> in the Comms Bay, despite your limited
experience in the field. You recall that a <span class="b i">significant portion of space
communication is conducted using <a href="https://en.wikipedia.org/wiki/Morse_code">
Morse Code</a></span>.</p>

<p>Although you've heard of Morse Code in passing, your understanding of it is a bit
hazy. With a sense of urgency, you frantically search your desk drawer, and lo and
behold! Serendipity leads you to a weathered booklet with yellowing pages titled
<span class="b i">"Deciphering Morse Code" a TopNet <span class="ssm">
(_ ___ .__. _. . _)</span> Retroflex Inc. Publication</span>. Inside, you discover a 
comprehensive <span class="b i">table</span> containing Letter-to-Morse Code translations,
along with a detailed guide on how your machine interprets the input code:</p>

<div class="flex-container shadow">
 <ul><li>
  Letters in the words will be separated by <span class="b i">spaces</span>
 </li><li>
  Words will be separated by <span class="b i"> new lines</span>(\\n)
 </li><li>
  Dashes (dahs) will be represented by <span class="b i">underscore</span> characters (_)
 </li><li>
  Dots (dits) will be represented by <span class="b i"> decimal point</span> characters (.)
 </li><li>
  Dots and dashes for each letter or character will <span class="b i">not</span> have
  spaces between them
 </li></ul></div>

<div class="imgcontainer pad"><table><thead><tr><th>
Letter</th><th>Code</th><th>Letter</th><th></th><th>Letter</th><th>Code</th></tr></thead>
<tbody><tr><td>A</td><td>._</td><td>K</td><td>_._</td><td>U</td><td>.._</td></tr>
<tr><td>B</td><td>_...</td><td>L</td><td>._..</td><td>V</td><td>..._</td></tr>
<tr><td>C</td><td>_._.</td><td>M</td><td>__</td><td>W</td><td>.__</td></tr>
<tr><td>D</td><td>_..</td><td>N</td><td>_.</td><td>X</td><td>_.._</td></tr>
<tr><td>E</td><td>.</td><td>O</td><td>___</td><td>Y</td><td>_.__</td></tr>
<tr><td>F</td><td>.._.</td><td>P</td><td>.__.</td><td>Z</td><td>__..</td></tr>
<tr><td>G</td><td>__.</td><td>Q</td><td>__._</td><td>.</td><td>._._._</td></tr>
<tr><td>H</td><td>....</td><td>R</td><td>._.</td><td>?</td><td>..__..</td></tr>
<tr><td>I</td><td>..</td><td>S</td><td>...</td><td>!</td><td>_._.__</td></tr>
<tr><td>J</td><td>.___</td><td>T</td><td>_</td><td>-</td><td>_...._</td></tr></tbody>
</table></div>

<h4> For example:</h4>

<span class="code" style="font-family: 'Roboto Mono', monospace;"> .._. .. ._. ... _ 
<br/> _.. ._ .__ _. </span><p>results in "FIRST DAWN".</p>

<p>Each word is separated by a new line character and each letter in the words "FIRST"
and "DAWN" are separated by a space, but there are no spaces between the Morse Code
dashes and dots of individual letters:</p>

<p>You decide that you should quickly make a Python script which reads the input from the
machine and decodes the Morse Code into text. Just in time, too, because the first message
is already coming in...</p>""",
                        instructions='Decode the message:',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n What is the message?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  SHE WILL RISE. HER LIGHT WILL BLIND THE STARS.\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=1,
                        sub_entry_id=2,
                        title='Something Alien...',
                        content="""<p>Just as you translate the question you received, another source sends a reply. This
must be the answer to the question asked in Part 1, but the contents of the new message
cause your script to error. This is not Morse Code; it looks like
<span class="b i">something alien</span>.</p>

<p>Rather than panic and run to your supervisor, you set your mind toward solving this
problem on your own. You re-read your Morse Code booklet to no avail and open your desk
drawer to see if there might be anything else in there that could be of use… Nothing.</p>

<p>Sighing heavily and putting your head in your hands, you catch a glimpse of a poster
on the wall beside your monitor, which you hadn't noticed before. It's titled with the
mnemonic device, <span class="b i">"O.B.M.T. for Alien Communication"</span>, and it
reads:</p>

<ol><li>
  Convert each character to its <span class="b i">Ordinal</span>
  <span class="sm">(Unicode code points)</span>
</li><li>
  Concatenate those numbers to one large integer, then into
  <span class="b i">Binary</span>
</li><li>
  Convert the Binary number into <span class="b i">Morse Code</span>
  <span class="sm">(considering the 0s dits and the 1s dahs)</span>
</li><li>
  Convert the Morse Code into <span class="b i">Text</span>
</li></ol>Underneath the fourth step there's a footnote:

<p class="shadow pad"><span class="b i">※ Alien communication is always only one
word</span>. Each received alien transmission has <span class="b i">three
<a href="https://en.wikipedia.org/wiki/Exclamation_mark">Exclamation Marks</a> at both
the start and end of the message</span>, with <span class="b i"> one Exclamation Mark
between each letter</span>.</p>

<h4>Here's an example of the alien input</h4>

<span class="code">※ƉΰـᒠW౻</span>
<ol><li>
  Converting each character it's Ordinal, you get<br/>
  <span class="code part sm" style="direction:ltr; unicode-bidi:bidi-override;">
  ※=8251 Ɖ=393 ΰ=944 ـ=1600 ᒠ=5280 W=87 ౻=3195</span>
</li><li>
  Concatenating those numbers to one large integer<br/>
  <span class="code part sm">825139394416005280873195</span><br/>
  and converting that number to Binary, you get<br/>
  <span class="code part sm">1010111010111010111001010110110101110101
   <br class="mbl"/>0111101010110101011010101011101011101011</span>
</li><li>
  Converting the Binary into Morse Code, you would get<br/>
  <span class="code part sm" style="font-family: 'Roboto Mono', monospace;">
   _._.___._.___._.___.._._.__.__._.___._._.__<br class="mbl"/>
   __._._.__._._.__._._._.___._.___._.__</span><br/>
  Removing the exclamation marks on both ends and between each letter, you get<br/>
  <span class="code part sm" style="font-family: 'Roboto Mono', monospace;">
  (!)\xa0\xa0\xa0(!)\xa0\xa0\xa0(!)\xa0\xa0_..\xa0(!)\xa0\xa0._\xa0(!)\xa0\xa0_.\xa0(!)
   <br class="mbl"/>
   __.\xa0(!)\xa0\xa0.\xa0(!)\xa0\xa0._.\xa0(!)\xa0\xa0\xa0(!)\xa0\xa0\xa0(!)</span>
  <br/>or
  <span class="code part sm" style="font-family: 'Roboto Mono', monospace;">
   _.. ._ _. __. . ._.</span>
</li><li>
  Converting this Morse Code into text gives you:<br/>
  <span class="code part">DANGER</span>
</li></ol>

<p>So <span class="code part">※ƉΰـᒠW౻</span>translates to
<span class="code part">DANGER</span><br/></p>

<p>You think you've got the hang of this! Time to decode the alien message...</p>

""",
                        instructions='The message you received is:',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n What is the alien reply?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  EOS\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=2,
                        sub_entry_id=1,
                        title='What a Mess!',
                        content="""<p>You wake, ready to start a new day. Your
<a href="https://en.wikipedia.org/wiki/Holographic_display">holographic tablet</a> dings,
displaying a message:</p>

<p class="shadow pad">Rise and shine, Cadet! Due to your exemplary performance in the
Comms Bay, we are assigning you to the Electrical Control Room. Report there at 0800
hours.</p>

<p>When you arrive, the room is in chaos. The crew are grabbing at piles of loose paper,
which completely cover the floor. The pages seem to be from an instruction manual of
sorts. Someone sees you standing there and tells you to grab some paper and
<span class="b i">sort them</span>, leaving before you can ask any questions. You grab a
pile.</p>

<p>The sheets of printed paper do not have page numbers, but they all have a
<span class="b i">header</span>printed at the top:</p>

<p class="header shadow pad b i">Section Title, Chapter Number, Subchapter Letter,
Section Number</p>

<p>Your puzzle input is a TXT file with the each page's header on individual lines. You
decide to sort the pages like any book — first by chapter, then by subchapter, then by
section. Each category sorted in ascending order. <span class="i">Chapter number and 
section number should be sorted as integers, not strings</span>.</p>

<p>When everyone is done sorting their piles, you assume you will have to work together
to combine all your piles into one, so you decide to create a
<a href="https://en.wikipedia.org/wiki/Mnemonic">mnemonic</a> out of the
<span class="b i">first letters of the sorted Section Titles</span> to help you 
contribute to this collaboration.</p>

<h4>For example:</h4><p>If your pages are</p>

<span class="code free">
 title,chapter,subchapter,section
 <br/>
 Cosmos,2,J,3
 <br/>
 Planets,2,A,9
 <br/>
 Exploration,3,Y,2
 <br/>
 Stars,1,X,4
 <br/>
 Astronauts,2,J,1
</span>

<p>You would sort them first by Chapter Number, then by Subchapter Letter, and finally
by Section Number to get</p>

<span class="code free">
 ["Stars", "1", "X", "4"]
 <br/>
 ["Planets", "2", "A", "9"]
 <br/>
 ["Astronauts", "2", "J", "1"]
 <br/>
 ["Cosmos", "2", "J", "3"]
 <br/>
 ["Exploration", "3", "Y", "2"]
</span>

<p>And the first letters of the Section Titles would spell out<span class="b i">
"SPACE"</span>.</p>

<p>The rest of the crew are almost done. You should quickly sort your pile of pages.</p>""",
                        instructions='Your pages are:',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n What do the first letters of your Section Titles spell?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i sm">\n  EXPLORING_THE_COSMOS:_AN_INCREDIBLE_JOURNEY_THROUGH_SPACE_ONE_GALAXY_AT_A_TIME.\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=2,
                        sub_entry_id=2,
                        title='BrailLED',
                        content="""<p>Now that that's all sorted, no pun intended, it's time to get to work. The stress
of this new assignment, caused by the chaos of the paper storm, has left you feeling
overwhelmed. It seems like the Electric Control Room might not be the place for you. You
should put in a <span class="b i">Change of Assignment request</span> with the Operations
Manager, but you've left your holographic tablet in your bunk. That's okay, because 
aboard the ship, all devices have the capability of communicating with the Operations 
Manager, provided there's a screen to display the reply.</p>

<p>Luckily for you, you're stood in front of the <span class="b i">
"Binary\xa0Represented\xa0All‑Inclusive\xa0Lettering\xa0LED"</span> System, or
<span class="b i">"BrailLED"</span> for short.</p>

<p>The BrailLED is a long strip of
<a href="https://en.wikipedia.org/wiki/Light-emitting_diode">LED lights</a>,
totaling <span class="b i">six rows</span> and <span class="b i">fifty‑two columns</span>
of individual lights.</p>

<div class="imgcontainer shadow pad"><img src="../static/images/02/strip.png"/></div>

<p>Transmissions are sent to the LED lights as <span class="b i">a packet of tuples</span>.
The first item of the tuple is a binary string and the second is a column header.
<ul><li>
   The BrailLED display Columns, from left to right, are labeled with the sorted 
   uppercase letters, A‑Z,followed by the sorted lowercase letters, a‑z.
</li><li>
   For each column, the binary string fills the column from top to bottom, assigning the 
   individual lights in that column <span class="b i">ON for 1</span> or
   <span class="b i">OFF for 0</span>.
</li></ul></p>

<div class="flex-container shadow"><div class="column"><div class="imgcontainer">
<img src="../static/images/02/braille.png"/></div></div>

<div class="column"><p class="column-content">The resulting LED display is a
<span class="b i">two‑row, 26‑column strip of 3x2 light groupings,</span> each grouping 
representing one letter in <a href="https://en.wikipedia.org/wiki/Braille">braille</a>
(diagram on the left).</p><span class="spacer"><br/></span>

<p class="column-content">The message is then read by interpreting the first line of 
26 braille symbols and then the second line, without any additional spaces.</p></div></div>

<p>Someone must have bumped the BrailLED amidst all the confusion this morning, because
the inputs are not coming in sorted. You will have to sort the inputs by their column 
header first before letting the LED display show you your message in braille.</p>

<h4>For example (with a shorter 6-column display):</h4>

<div class="imgcontainer"><p>If the transmission you receive is
  <span class="code free">
   000110,c<br/>
   000010,a<br/>
   111100,C<br/>
   111101,A<br/>
   100011,b<br/>
   100110,B</span></p></div>

<div class="imgcontainer">You would sort it
 <span class="code free">
  111101,A<br/>
  100110,B<br/>
  111100,C<br/>
  000010,a<br/>
  100011,b<br/>
  000110,c</span></div>

<p>Column A is, from top to bottom, <span class="code part">111101</span> making the lights
<span class="code part">ON ON ON ON OFF ON</span></p>

<p>Filling in all of the columns, your BrailLED Display would look like this:</p>

<div class="imgcontainer"><img class="smallpic" src="../static/images/02/sample.png"/></div>

<p>Reading left to right, top to bottom, starting with the first row we have the braille
<span style="font-size: xx-large"> ⠏⠇⠁⠝⠑⠞ </span>which spells <span class="code part">
 PLANET</span>.</p>

<p>Your transmission is coming in now. Will you be given a new assignment for tomorrow?</p>""",
                        instructions='Here is your received transmission:',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n What does the braille on the panel spell out?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  CADET YOUR NEXT MISSION IS LOCATED IN THE CARGO HOLD\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=3,
                        sub_entry_id=1,
                        title='Stop, Dock, and Roll',
                        content="""<p>Today, you head to the Cargo Hold for your next assignment. The room is brightly
lit in a white light, and you see thick tubes and chutes crisscrossing the walls and
the high ceiling. Immediately in front of you, centered in the room, you see a
<span class="b i">row of 40 giant capsule-filled tubes</span> with an opening for each
at the very top and at the front of the bottom, like upside-down
<a href="https://en.wikipedia.org/wiki/Pez">PEZ dispensers</a>. Beside this dispensing
system, bolted to the floor, is a large
<a href="https://en.wikipedia.org/wiki/Robotic_arm">robotic arm</a>.
It is nearly as tall as the ceiling and features grips for spherical objects at the
end of its long arm.</p>

<p>You're greeted by the supervisor of the Cargo Hold, who has a kind voice and an
even kinder smile. She explains what you need to do:</p>

<p class="shadow pad">The <span class="b i">spherical capsules</span> inside these
tubes are all different kinds of cargo. They are heavy metallic balls studded with
rivets and embellishments. To tell them apart, most of the capsules are
<span class="b i">painted with a large, bright red character</span> (either
alphabetical or a punctuation symbol). The ones that lack any marking are all the
same item, so it might be helpful to think of them as a space character (" ").</p>

<p>What's inside them? She has no idea. She just gets a request from somewhere and
runs the machine to fulfill it. Requests come on a piece of paper with two sections.</p>

<ol><li>
  <span class="b i">The first line:</span> a number from 0 to 39.<br/> This indicates
  which dispenser to set the machine to <span class="b i">start</span> at.
</li><li>
  <span class="b i">The next line:</span> a series of commands for the robotic arm,
  separated by commas.<br/> Each command begins with <span class="b i">an R, L, T, or
  D</span>, followed by a<span class="b i">number</span>.
</li><li>
  <span class="b i">The following lines:</span> lines of text representing the initial
  state of capsules in all dispensers.<br/> Each line shows the contents of the
  dispensers, ordered from 0 to 39. The capsule characters are listed
  <span class="b i">from the bottom</span> of each dispenser <span class="b i">to
  the top</span>, separated by commas.
</li></ol>

<div class="shadow"><ul><li>
  When the machine gets an <span class="b i">R or L command</span>, the robotic arm
  moves its position either <span class="b">R</span>ight or <span class="b">
  L</span>eft by the numberof places indicated
</li></ul></div>

<div class="shadow"><ul><li>
  When the machine gets a <span class="b i">T command</span>, the robotic arm
  <span class="b">T</span>akes a single capsule from the dispenser at its current
  position from the bottom, letting the remaining capsules in the dispenser descend
  to fill the empty space
</li><li>
  The grabbed capsule is then vacuumed into the robotic arm's <span class="b i">C-shaped
  tube</span>, where capsules are stored, always inserting itself <span class="b i">
  into the entry point</span> of the tube
</li><li>
  This process is completed as many times as indicated by the number in the command,
  <span class="b i">always one-at-a-time</span> and never multiple capsules
  simultaneously
</li></ul></div>

<div class="shadow"><ul><li>
  When the machine gets a <span class="b i">D command</span>, the robotic arm
  <span class="b">D</span>rops the specified number of capsules, one-at-a-time, into
  the top of the dispenser it's currently facing
</li><li>
  Because of the C-shaped tube, capsules are dispensed from the <span class="b i">
  opposite end</span> of the tube
</li></ul></div>

<p>You need to manually control the machine while following the instructions. Once the
order is complete, you press the "release" button and <span class="b i">one capsule
from each dispenser</span> rolls out from the bottom, in order, onto the delivery cart
to be sent out to the appropriate area of the ship.</p>

<h4>For example (with a shorter 5-dispenser system):</h4>

<p>If your instructions are <span class="code free">
 3<br/>
 L1,T3,R2,D1,L4,T3,R3,D4,L2,T1,L1,D1<br/>
 Y,R,S<br/>
 H,P<br/>
 F,C,B,A<br/>
 <br/>
 E</span></p>

<div class="flex-container mono sm"><div class="container-item"><table>
<caption>START</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P3">
<tr><td>0</td><td>1</td><td>2</td><td class="select">3</td><td>4</td></tr>
<tr><td></td><td></td><td>A</td><td></td><td></td></tr>
<tr><td>S</td><td></td><td>B</td><td></td><td></td></tr>
<tr><td>R</td><td>P</td><td>C</td><td></td><td></td></tr>
<tr><td>Y</td><td>H</td><td>F</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td>A</td><td></td><td></td></tr>
<tr><td>S</td><td></td><td>B</td><td></td><td></td></tr>
<tr><td>R</td><td>P</td><td>C</td><td></td><td></td></tr>
<tr><td>Y</td><td>H</td><td>F</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: T3</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>S</td><td></td><td></td><td></td><td></td></tr>
<tr><td>R</td><td>P</td><td></td><td></td><td></td></tr>
<tr><td>Y</td><td>H</td><td>A</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>C</td><td>F</td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: R2</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P4">
<tr><td>0</td><td>1</td><td>2</td><td>3</td><td class="select">4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>S</td><td></td><td></td><td></td><td></td></tr>
<tr><td>R</td><td>P</td><td></td><td></td><td></td></tr>
<tr><td>Y</td><td>H</td><td>A</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>C</td><td>F</td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: D1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P4">
<tr><td>0</td><td>1</td><td>2</td><td>3</td><td class="select">4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>S</td><td></td><td></td><td></td><td></td></tr>
<tr><td>R</td><td>P</td><td></td><td></td><td>F</td></tr>
<tr><td>Y</td><td>H</td><td>A</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>C</td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L4</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>S</td><td></td><td></td><td></td><td></td></tr>
<tr><td>R</td><td>P</td><td></td><td></td><td>F</td></tr>
<tr><td>Y</td><td>H</td><td>A</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>C</td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: T3</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td>P</td><td></td><td></td><td>F</td></tr>
<tr><td></td><td>H</td><td>A</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>S</td><td>R</td><td>Y</td><td>B</td><td>C</td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: R3</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P3">
<tr><td>0</td><td>1</td><td>2</td><td class="select">3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td>P</td><td></td><td></td><td>F</td></tr>
<tr><td></td><td>H</td><td>A</td><td></td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>S</td><td>R</td><td>Y</td><td>B</td><td>C</td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: D4</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P3">
<tr><td>0</td><td>1</td><td>2</td><td class="select">3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>R</td><td></td></tr>
<tr><td></td><td></td><td></td><td>Y</td><td></td></tr>
<tr><td></td><td>P</td><td></td><td>B</td><td>F</td></tr>
<tr><td></td><td>H</td><td>A</td><td>C</td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>S</td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L2</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P1">
<tr><td>0</td><td class="select">1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>R</td><td></td></tr>
<tr><td></td><td></td><td></td><td>Y</td><td></td></tr>
<tr><td></td><td>P</td><td></td><td>B</td><td>F</td></tr>
<tr><td></td><td>H</td><td>A</td><td>C</td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>S</td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: T1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P1">
<tr><td>0</td><td class="select">1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>R</td><td></td></tr>
<tr><td></td><td></td><td></td><td>Y</td><td></td></tr>
<tr><td></td><td></td><td></td><td>B</td><td>F</td></tr>
<tr><td></td><td>P</td><td>A</td><td>C</td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>H</td><td>S</td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>R</td><td></td></tr>
<tr><td></td><td></td><td></td><td>Y</td><td></td></tr>
<tr><td></td><td></td><td></td><td>B</td><td>F</td></tr>
<tr><td></td><td>P</td><td>A</td><td>C</td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>H</td><td>S</td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: D1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>R</td><td></td></tr>
<tr><td></td><td></td><td></td><td>Y</td><td></td></tr>
<tr><td></td><td></td><td></td><td>B</td><td>F</td></tr>
<tr><td>S</td><td>P</td><td>A</td><td>C</td><td>E</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>H</td><td></td><td></td><td></td><td></td></tr></tfoot></table></div></div>

<p>Then, pressing the release button will dispense one capsule from each dispenser, in
order, giving you the capsules: <span class="code part">SPACE</span>.</p>

<p>Let's get that first delivery out. Your instructions are right in front of you...</p>""",
                        instructions='Your instructions are:',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n Write the characters of the released capsules in order.\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  THE GODDESS IS COMING. TIME\'S ALMOST UP!\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=3,
                        sub_entry_id=2,
                        title='Blunder Belt',
                        content="""<p>"Stop, stop, stop, stop!" You see the supervisor running at full speed out of her 
office, frantically waving her arms. When she reaches you at the robotic arm, she pauses 
to catch her breath and says</p>

<p class="shadow pad">She's forgotten to tell you the <span class="b i">most important
step</span>! <span class="b i"> Each time the robot arm receives a Take command</span>,
after taking the correct number of capsules from the dispenser, you must
<span class="b i">push the "shift" button</span>. This button activates a
<a href="https://en.wikipedia.org/wiki/Conveyor_belt">conveyor belt</a> under all the
dispensers, <span class="b i">shifting their contents one space to the left</span>. The
contents of dispenser 12 move to dispenser 11, the contents of dispenser 1 move to
dispenser 0, and so on. The contents that were in dispenser 0 are displaced all the way
to the end, ending up in dispenser 39. The shift happens internally, and the
<span class="b i">robotic arm's position is not affected by this change</span>. If the
arm's position is 19, it remains 19 despite the contents of dispenser 19 changing. The
conveyor belt shift occurs only after Take commands; commands for Right, Left, or Drop do
not trigger the shift.</p>

<h4>For example (with a shorter 5-dispenser system):</h4>

<p>If your instructions are <span class="code free">
3<br/>
L1,T3,R1,D1,L3,T2,R4,D4,L2,T1,L2,D1<br/>
A,O,S<br/>
H,P<br/>
R,F,B,T<br/>
<br/>
C</span></p>

<div class="flex-container mono sm"><div class="container-item"><table>
<caption>START</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P3">
<tr><td>0</td><td>1</td><td>2</td><td class="select">3</td><td>4</td></tr>
<tr><td></td><td></td><td>T</td><td></td><td></td></tr>
<tr><td>S</td><td></td><td>B</td><td></td><td></td></tr>
<tr><td>O</td><td>P</td><td>F</td><td></td><td></td></tr>
<tr><td>A</td><td>H</td><td>R</td><td></td><td>C</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td>T</td><td></td><td></td></tr>
<tr><td>S</td><td></td><td>B</td><td></td><td></td></tr>
<tr><td>O</td><td>P</td><td>F</td><td></td><td></td></tr>
<tr><td>A</td><td>H</td><td>R</td><td></td><td>C</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: T3</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>S</td><td></td><td></td><td></td><td></td></tr>
<tr><td>O</td><td>P</td><td></td><td></td><td></td></tr>
<tr><td>A</td><td>H</td><td>T</td><td></td><td>C</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>F</td><td>R</td><td></td><td></td></tr></tfoot></table></div> 
<div class="container-item"><table><caption class="shift">SHIFT</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td></td><td>S</td></tr>
<tr><td>P</td><td></td><td></td><td></td><td>O</td></tr>
<tr><td>H</td><td>T</td><td></td><td>C</td><td>A</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>F</td><td>R</td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: R1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P3">
<tr><td>0</td><td>1</td><td>2</td><td class="select">3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td></td><td>S</td></tr>
<tr><td>P</td><td></td><td></td><td></td><td>O</td></tr>
<tr><td>H</td><td>T</td><td></td><td>C</td><td>A</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>F</td><td>R</td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: D1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P3">
<tr><td>0</td><td>1</td><td>2</td><td class="select">3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td></td><td>S</td></tr>
<tr><td>P</td><td></td><td></td><td>R</td><td>O</td></tr>
<tr><td>H</td><td>T</td><td></td><td>C</td><td>A</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>F</td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L3</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td></td><td>S</td></tr>
<tr><td>P</td><td></td><td></td><td>R</td><td>O</td></tr>
<tr><td>H</td><td>T</td><td></td><td>C</td><td>A</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>B</td><td>F</td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: T2</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td></td><td>S</td></tr>
<tr><td></td><td></td><td></td><td>R</td><td>O</td></tr>
<tr><td></td><td>T</td><td></td><td>C</td><td>A</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>P</td><td>H</td><td>B</td><td>F</td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption class="shift">SHIFT</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td>S</td><td></td></tr>
<tr><td></td><td></td><td>R</td><td>O</td><td></td></tr>
<tr><td>T</td><td></td><td>C</td><td>A</td><td></td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>P</td><td>H</td><td>B</td><td>F</td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: R4</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P4">
<tr><td>0</td><td>1</td><td>2</td><td>3</td><td class="select">4</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td>S</td><td></td></tr>
<tr><td></td><td></td><td>R</td><td>O</td><td></td></tr>
<tr><td>T</td><td></td><td>C</td><td>A</td><td></td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>P</td><td>H</td><td>B</td><td>F</td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: D4</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P4">
<tr><td>0</td><td>1</td><td>2</td><td>3</td><td class="select">4</td></tr>
<tr><td></td><td></td><td></td><td></td><td>P</td></tr>
<tr><td></td><td></td><td></td><td>S</td><td>H</td></tr>
<tr><td></td><td></td><td>R</td><td>O</td><td>B</td></tr>
<tr><td>T</td><td></td><td>C</td><td>A</td><td>F</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L2</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td>P</td></tr>
<tr><td></td><td></td><td></td><td>S</td><td>H</td></tr>
<tr><td></td><td></td><td>R</td><td>O</td><td>B</td></tr>
<tr><td>T</td><td></td><td>C</td><td>A</td><td>F</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: T1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td></td><td>P</td></tr>
<tr><td></td><td></td><td></td><td>S</td><td>H</td></tr>
<tr><td></td><td></td><td></td><td>O</td><td>B</td></tr>
<tr><td>T</td><td></td><td>R</td><td>A</td><td>F</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>C</td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption class="shift">SHIFT</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P2">
<tr><td>0</td><td>1</td><td class="select">2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>P</td><td></td></tr>
<tr><td></td><td></td><td>S</td><td>H</td><td></td></tr>
<tr><td></td><td></td><td>O</td><td>B</td><td></td></tr>
<tr><td></td><td>R</td><td>A</td><td>F</td><td>T</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>C</td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: L2</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>P</td><td></td></tr>
<tr><td></td><td></td><td>S</td><td>H</td><td></td></tr>
<tr><td></td><td></td><td>O</td><td>B</td><td></td></tr>
<tr><td></td><td>R</td><td>A</td><td>F</td><td>T</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td>C</td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>
<div class="container-item"><table><caption>Command: D1</caption><thead>
<tr><th colspan="5">Dispensers:</th></tr></thead><tbody class="P0">
<tr><td class="select">0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
<tr><td></td><td></td><td></td><td>P</td><td></td></tr>
<tr><td></td><td></td><td>S</td><td>H</td><td></td></tr>
<tr><td></td><td></td><td>O</td><td>B</td><td></td></tr>
<tr><td>C</td><td>R</td><td>A</td><td>F</td><td>T</td></tr></tbody><tfoot>
<tr><th colspan="5">C-Shaped Tube:</th></tr>
<tr><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div></div>

<p>Then, pressing the release button will dispense one capsule from each dispenser, in
order, giving you the capsules: <span class="code part">CRAFT</span>.</p>

<p>The supervisor pushes a big red reset button, which empties the robot arm and
dispensers and fills the dispensers back up again with their predetermined order.
"Now you can start again", she says, and hands you a new instruction sheet.</p>""",
                        instructions='Your instructions are:',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n Write the characters of the released capsules in order.\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  FUEL UP CADET.YOU\'LL NEED YOUR STRENGTH.\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=4,
                        sub_entry_id=1,
                        title='The Center of Flavor',
                        content="""<p>It's a new day on the STS Solara, and today you're headed to the
<a herf="https://en.wikipedia.org/wiki/Galley_(kitchen)">galley</a>. That's perfect,
because you could use a snack…</p>

<p>You meet the ship's head chef, who is deep in thought about the menu. Just as you're
about to mention that you could really go for a cheeseburger, he begins speaking to you,
explaining what's on his mind.</p>

<p>It turns out, the <span class="b i">only food</span> that the crew actually eats
aboardthe ship is <span class="b i">Galactic
<a href="https://en.wikipedia.org/wiki/Algae">Algae</a> Blooms</span>; a thought which
slightly turns your stomach, but you hide your disgust well.</p>

<p>There are <span class="b i">five species</span> of Galactic Algae Blooms:
<span class="b i">Sweet, Bitter, Umami, Salty, and Sour</span>. The depth of flavor of
each of these species varies from bloom to bloom, each having its own scores for both
<span class="b i">flavor complexity, persistence of taste, and intensity</span>. A
skilled chef can take these individual flavor profiles and create dishes that resemble
many non-algae-based dishes the crew are familiar with from home.</p>

<p>The process is as follows:</p><div class="shadow pad">
<ol><li>
  <span class="b i">Gather algae from each of the required species</span>:
</li><ul><li>
  You select three individual algae blooms (your puzzle input) and obtain each of their
  flavor profiles.
</li><li>
  Flavor complexity is labeled X, so the three algae blooms you would use of a certain
  species have x1, x2, and x3.
</li><li>
  Persistence of taste is labeled Y; y1, y2, and y3.
</li><li>
  Intensity is cleverly labeled m for "Mmm". Each algae bloom has its own individual
  intensity; m1, m2, and m3.
</li><li>
  Each line of your input represents a species of Galactic Algae Bloom.
  <span class="b i">Individual algae blooms are separated by spaces</span>. For each
  individual algae bloom, the format is
  Intensity(Flavor\xa0Complexity,Persistence\xa0of\xa0taste) or <span class="b i">
  m(x,y)</span>.
</li></ul><li>
  <span class="b i">Seek out the Center of Flavor for each species</span>:
</li><ul><li>
  To determine the Center of Flavors of a species with three individual algae blooms,
  you use the common <span class="b i">Center of Mass</span>(cm) equations.
</li></ul></ol>
  <div class="imgcontainer pad"><img src="../static/images/04/CoMx_simple.png"/></div>
  <div class="imgcontainer pad"><img src="../static/images/04/CoMy_simple.png"/></div>
<ol><ul><li>
  Finding the Center of Flavor at X and at Y will provide you with the Center of Flavor
  coordinates on the complexity-persistence graph. You will have a set of coordinates
  for each species used in the recipe.
</li></ul><li>
  <span class="b i">Lookup the values in the ASCII Recipe Cards</span>:
</li><ul><li>
  Translating the <span class="b i">numerical value</span> of each coordinate
  <span class="b i">to its ASCII</span> value will provide you with two letters per
  species of Galactic Algae Blooms. One letter for X and one letter for Y.
</li></ul><li>
  <span class="b i">Complete the recipe</span>:
</li><ul><li>
  Concatenating the letters for all the X coordinates in order, a space, and all the 
  letters for the Y coordinates in order, will spell out the recipe item.
</li></ul></ol></div>

<h4>For example:</h4>

<p>If the algae blooms you gather from three species of Galactic Algae Blooms is
<span class="code free">
6(71,74) 6(70,73) 3(68,76)<br/>
12(74,65) 8(73,63) 4(70,69)<br/>
8(75,80) 4(72,71) 18(69,77)</span></p>

<p>To get the Center of Mass at X for the first species, you would put the numbers into
the equation:<br/>for the numerator <span class="code part">(6*71) + (6*70) + (3*68) = 
1050</span><br/> and the denominator <span class="code part">6 + 6 + 3 = 15</span>
giving you <span class="code part">1050/15</span><br/><span class="code part">70</span>
for the X value.</p>

<p>To get the Center of Mass at Y for the first species, you would put the numbers into
the equation:<br/>for the numerator <span class="code part">(6*74) + (6*73) + (3*76) =
1110</span>.<br/>The denominator remains the same as for X, <span class="code part">
15</span> giving you <span class="code part">1110/15</span><br/>
<span class="code part">74</span> for the Y value.</p>

<p>Performing the same operations on all three species, we get X and Y values:
<span class="code part">(70, 74), (73, 65), and (71, 77)</span></p>

<p>Converting these numbers to ASCII values, you get: <span class="code part">(F, J),
(I, A), and (G, M)</span></p>

<p>Finally, concatenating all of the X values and Y values with a space between them,
you get: <span class="code part">FIG JAM</span></p>""",
                        instructions='Here are your selected Galactic Algae Blooms:',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n What recipe will this make?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  GREEN SALAD\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=4,
                        sub_entry_id=2,
                        title="Gone Fishin'",
                        content="""<p>Now that you have a recipe in mind, it's time to gather the Galactic Algae Blooms
from deep space. You do this using a <span class="b i">deep space net</span>. The chef
shows you the control panel for the net, a big screen displaying glowing blobs in a
gradient of color. These blobs represent <span class="b i"> clusters of Galactic Algae
Blooms</span>. Pressing the toggle button will alternate between displaying the algae
cluster blobs and <span class="b i">a
<a href="https://computersciencewiki.org/index.php/Two-dimensional_arrays">
grid</a> of numbers</span>, your puzzle input, representing how many algae blooms are
at each point in space.</p>

<p>The cost of casting this deep space net is very high, so you are informed you can
<span class="b i">only cast once per day</span>. Fortunately, the algae blooms migrate
around each cluster's <span class="b i">center of mass</span>, so casting the net
directly into that location will <span class="b i">collect every algae bloom from that
cluster</span>. Since the STS Solara has a large crew, you should aim to collect as
many algae blooms as possible.</p>

<p>In your previous equations for the Center of Mass, you had only 3 points to consider,
but these clusters of algae blooms are much more numerous. Unfortunately, the previous
equation will not work, but you notice that you can perform the summations in the
numerator and the denominator of the equations with any number of points.
<span class="b i">You can use these new equations</span>. (Sigma Σ, here, meaning "the
sum for values from 1 to N".)</p>

<div class="imgcontainer pad"><a href="../static/images/04/CoMx_sum.png">
<img class="smallpic pad" src="../static/images/04/CoMx_sum.png"/></a>
<span class="spacer"> </span><a href="../static/images/04/CoMy_sum.png">
<img class="smallpic pad" src="../static/images/04/CoMy_sum.png"/></a></div>

<p>Type the <span class="b i">X and Y coordinates without spaces, separated by a
comma</span>, into the machine to cast the net into the cluster with the greatest total
mass.</p>

<h4>For example:</h4><div class="flex-container"><div class="container-item">
<p>This blob</p><img class="midpic" src="../static/images/04/example.png"/></div>

<div class="container-item"><p>gives you the following number grid</p>
<span class="code free sm">
0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,3<br/>
0,0,0,0,5,6,3,0,0,1,2,2,0,0,0,0,0,0,2,7<br/>
0,0,0,2,8,9,9,6,4,5,4,2,0,0,0,0,0,1,5,8<br/>
0,0,0,1,8,9,9,9,9,8,6,2,0,0,0,0,0,3,4,5<br/>
0,0,0,0,4,8,9,8,9,8,6,2,0,0,0,0,1,3,2,0<br/>
0,0,0,0,0,2,3,3,5,7,6,2,0,0,0,0,1,2,0,0<br/>
0,0,0,0,0,0,0,0,2,4,5,2,0,0,0,0,1,1,0,0<br/>
0,0,0,0,0,0,0,0,0,1,3,1,0,0,0,0,1,2,0,0<br/>
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3,2,0<br/>
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,5<br/>
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,5,7<br/>
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,6<br/>
0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,2<br/>
0,0,0,0,4,5,2,0,0,0,0,2,3,2,0,0,0,0,0,0<br/>
0,0,0,1,7,8,5,1,0,0,4,8,9,7,3,0,0,0,0,0<br/>
0,0,0,1,7,8,4,0,0,1,6,9,9,9,6,1,0,0,0,0<br/>
0,0,0,1,6,5,2,0,0,0,3,8,9,8,6,3,1,0,1,2<br/>
0,0,0,2,4,3,0,0,0,0,0,2,3,3,2,2,1,1,1,1<br/>
0,0,2,4,5,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0<br/>
1,2,4,6,5,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0<br/></span></div>

<div class="container-item"><p>You can see the clusters' values easier by ignoring the
0s</p><span class="code free sm">
, , , ,1,1, , , , ,1,1, , , , , , , ,3<br/>
, , , ,5,6,3, , ,1,2,2, , , , , , ,2,7<br/>
, , ,2,8,9,9,6,4,5,4,2, , , , , ,1,5,8<br/>
, , ,1,8,9,9,9,9,8,6,2, , , , , ,3,4,5<br/>
, , , ,4,8,9,8,9,8,6,2, , , , ,1,3,2,<br/>
, , , , ,2,3,3,5,7,6,2, , , , ,1,2, ,<br/>
, , , , , , , ,2,4,5,2, , , , ,1,1, ,<br/>
, , , , , , , , ,1,3,1, , , , ,1,2, ,<br/>
, , , , , , , , , , , , , , , ,1,3,2,<br/>
, , , , , , , , , , , , , , , , ,4,4,5<br/>
, , , , , , , , , , , , , , , , ,2,5,7<br/>
, , , , , , , , , , , , , , , , , ,2,6<br/>
, , , ,1,1, , , , , , , , , , , , , ,2<br/>
, , , ,4,5,2, , , , ,2,3,2, , , , , ,<br/>
, , ,1,7,8,5,1, , ,4,8,9,7,3, , , , ,<br/>
, , ,1,7,8,4, , ,1,6,9,9,9,6,1, , , ,<br/>
, , ,1,6,5,2, , , ,3,8,9,8,6,3,1, ,1,2<br/>
, , ,2,4,3, , , , , ,2,3,3,2,2,1,1,1,1<br/>
, ,2,4,5,2, , , , , , , , , , , , , ,<br/>
1,2,4,6,5,1, , , , , , , , , , , , , ,<br/></span></div></div>

<p>Looking at the C-shaped cluster on the right, you can calculate the
<span class="b i">total mass</span> by adding all of the individual masses in the cluster.
<span class="code part">
3+2+7+1+5+8+3+4+5+1+3+2+1+2+1+1+1+2+1+3+2+4+4+5+2+5+7+2+6+2 = 95</span></p>

<p>Then for the numerator of the Center of Mass equation for X, you can multiply every
mass by its X position <span class="b i">(m*x)</span> and sum the results.
<span class="code part">
(3*19)+(2*18)+(7*19)+(1*17)+(5*18)+(8*19)+(3*17)+(4*18)+(5*19)+(1*16)+(3*17)+(2*18)+(1*16)+(2*17)+(1*16)+(1*17)+(1*16)+(2*17)+(1*16)+(3*17)+(2*18)+(4*17)+(4*18)+(5*19)+(2*17)+(5*18)+(7*19)+(2*18)+(6*19)+(2*19)
<br/> = 1722</span> Since you are looking for an integer position on the grid, you can
use integer division to get the Center of Mass' position at X. You take the numerator
you just calculated, and divide it by the total mass in the denominator.<br/>
<span class="code part">1722 // 95 = 18</span></p>

<p>You do the same for the Y positions <span class="b i">(m*x)</span> for the Center of
Mass equation for Y. <span class="code part">
(3*0)+(2*1)+(7*1)+(1*2)+(5*2)+(8*2)+(3*3)+(4*3)+(5*3)+(1*4)+(3*4)+(2*4)+(1*5)+(2*5)+(1*6)+(1*6)+(1*7)+(2*7)+(1*8)+(3*8)+(2*8)+(4*9)+(4*9)+(5*9)+(2*10)+(5*10)+(7*10)+(2*11)+(6*11)+(2*12)
<br/> = 562</span> <span class="code part">562 // 95 = 5</span>, so the Center of Mass
for that cluster is at <span class="code part">position (18,5) with a total mass of
95</span>.</p>

<p>Doing the same for all clusters, you get</p>
<span class="code free">
CoM (7,3) total mass: 233,<br/>
CoM (18,5) total mass: 95,<br/>
CoM (4,15) total mass: 110,<br/>
CoM (12,15) total mass: 136</span>

<p>Shown on the diagram with stars for the location of each Center of Mass:</p>
<img class="midpic" src="../static/images/04/example_results.png"/>

<p>You can see that 233 is the cluster with the greatest mass, so you would input
<span class="code part">7,3</span> into the coordinates for the deep space net.</p>""",
                        instructions='The deep space net\'s control panel displays your actual clusters:\n<br/>\n<a href="../static/images/04/figure.png">\n <img class="midpic" src="../static/images/04/figure.png"/>\n</a>\n<br/>\nYou press the toggle button and get the following number grid (your puzzle input):',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n What are the coordinates you should type in?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  177,136\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=5,
                        sub_entry_id=1,
                        title='Pixel Perfect Panic',
                        content="""<p>You performed so well in the galley that the crew in the generator room has
requested your help today. Their <span class="b i">Power Harvester machine</span>,
which <span class="b i">gathers energy from nearby stars to fuel the ship</span>, is
functioning fine. However, they are having <span class="b i">trouble reading the outputs
</span> that indicate how many gigajoules(GJ) of energy have been collected.</p>

<p>Here's how the Power Harvester works:<br/>
After sending a <a href="https://en.wikipedia.org/wiki/Photon">photon</a> collection 
beam toward a star, the energy from that star is gathered and stored in one of the power
tanks in the generator room. Although the Power Harvester is somewhat outdated, it has
been reliable over the years with minimal updates. <span class="b i">Instead of a digital
display, this antique machine <a href="https://en.wikipedia.org/wiki/Extrusion">extrudes</a>
a long, thin wire of singular <a href="https://en.wikipedia.org/wiki/Pixel">
pixels</a></span>. This wire is then <span class="b i">fed into the more modern P.I.L.
(Patterned Image Layout) System, which reconstructs it into a square image</span>. The
resulting image displays the number of GJ harvested.</p>

<p>Despite its age, the Power Harvester is known for its good old-fashioned reliability
and continues to run smoothly. However, <span class="b i"> the P.I.L. System is failing
</span> and can no longer reconstruct the wire into a viewable square image. You need to
<span class="b i">reprogram it to restore this function</span>.</p>

<ul><li class="pad">
  You can be certain that <span class="b i">the length of wire extruded from the Power
  Harvester machine is a <a href="https://en.wikipedia.org/wiki/Square_number">perfect
  square</a></span>, which means that it can be arranged into an image with
  <span class="b i">equal width and height</span>.
</li><li>
  To create the image, <span class="b i">start at point (0,0)</span> and lay wire
  <span class="b i">to the right until you reach the end of the row</span>, indicated by
  the width of the desired square image. Then, <span class="b i">move down a row</span>
  and <span class="b i">lay the wire to the left</span>,
  <a href="https://en.wikipedia.org/wiki/Zigzag">zigzagging</a> from top to bottom and
  left to right until the entire wire is used.
</li></ul>

<h4>For example:</h4>

<p>The wire with pixels</p>

<div><table class="map"><tr>
<td style="background-color:darkgreen;">0</td>
<td style="background-color:darkblue">1</td>
<td style="background-color:purple">2</td>
<td style="background-color:indigo">3</td>
<td style="background-color:darkgreen;">4</td>
<td style="background-color:darkblue;">5</td>
<td style="background-color:purple;">6</td>
<td style="background-color:indigo;">7</td>
<td style="background-color:darkgreen;">8</td>
<td style="background-color:darkblue;">9</td>
<td style="background-color:purple;">10</td>
<td style="background-color:indigo;">11</td>
<td style="background-color:darkgreen;">12</td>
<td style="background-color:darkblue;">13</td>
<td style="background-color:purple;">14</td>
<td style="background-color:indigo;">15</td>
</tr></table></div>

<p>would zigzag into the following formation</p>
<div class="flex-container"><div class="container-item"><table class="map"><tr>
<td style="background-color:darkgreen;">0</td>
<td style="background-color:darkblue">1</td>
<td style="background-color:purple">2</td>
<td style="background-color:indigo;">3</td></tr><tr>
<td style="background-color:indigo;">7</td>
<td style="background-color:purple">6</td>
<td style="background-color:darkblue">5</td>
<td style="background-color:darkgreen;">4</td></tr><tr>
<td style="background-color:darkgreen;">8</td>
<td style="background-color:darkblue">9</td>
<td style="background-color:purple">10</td>
<td style="background-color:indigo;">11</td></tr><tr>
<td style="background-color:indigo;">15</td>
<td style="background-color:purple">14</td>
<td style="background-color:darkblue">13</td>
<td style="background-color:darkgreen;">12</td></tr></table></div>

<div class="spacer"><span class="b lg">or</span></div>
<div class="container-item"><img class="smallpic" src="../static/images/05/linea.png"/>
</div></div>

<p>A larger wire with more pixels might produce an image like</p><div class="imgcontainer">
<img src="../static/images/05/sample.png" style="height:50px;width:50px;"/></div>

<p>making the amount of energy obtained by the Power Harvester <span class="code part">
79</span>GJ.</p>""",
                        instructions='Here is your extruded wire:',
                        input_type='png',
                        form='<label class="main" for="answer1">\n How many GJ of energy have been harvested?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  7462\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=5,
                        sub_entry_id=2,
                        title='Diamond in the Data Rough',
                        content="""<p>In addition to harvesting gigajoules of power from the stars, <span class="b i">
the Power Harvester also collects diamond gas</span> as a side effect.</p>

<p>When compressed, this gas forms actual 
<a href="https://en.wikipedia.org/wiki/Diamond">diamonds</a>, which can be sold — likely
another reason why this antique machine remains so popular. The diamond gas is filtered
into separate containers, and the resulting diamonds help finance the missions of the
STS Solara.</p>

<p>Fortunately, the Power Harvester also <span class="b i">tracks the amount of diamond
gas collected in liters</span>, which is <span class="b i">indicated on the same
extruded wire</span>. Once again, the task of generating an image to display the total
liters of diamond gas falls to the P.I.L System, which is still buggy.
<span class="b i">You'll need to reprogram it yet again to shape the wire into a new
formation and read the amount of diamond gas</span>.</p>

<ul><li>
  To create this new image formation, <span class="b i">use the same wire</span>.
  Instead of zigzagging from left to right and top to bottom, <span class="b i">zigzag
  diagonally from the upper left corner (point (0,0)) to the bottom right corner</span>.
</li><li>
  <span class="b i">Start at point (0,0)</span> and <span class="b i">lay the wire 1
  pixel right</span>, then <span class="b i">move diagonally down-left</span>. After
  completing one diagonal line down-left, <span class="b i">lay the wire 1 pixel down
  </span> and <span class="b i">move diagonally up-right</span>. This process continues
  until the entire wire is used.
</li><li>
  If the height is reached, the wire will move right instead of down before moving
  up-right. If the width is reached, the wire will move down instead of right before
  moving down-left.
</li></ul>

<h4>For example:</h4>

<p>The same wire as before, with pixels</p>
<div><table class="map"><tr>
<td style="background-color:darkgreen;">0</td>
<td style="background-color:darkblue">1</td>
<td style="background-color:purple">2</td>
<td style="background-color:indigo">3</td>
<td style="background-color:darkgreen;">4</td>
<td style="background-color:darkblue;">5</td>
<td style="background-color:purple;">6</td>
<td style="background-color:indigo;">7</td>
<td style="background-color:darkgreen;">8</td>
<td style="background-color:darkblue;">9</td>
<td style="background-color:purple;">10</td>
<td style="background-color:indigo;">11</td>
<td style="background-color:darkgreen;">12</td>
<td style="background-color:darkblue;">13</td>
<td style="background-color:purple;">14</td>
<td style="background-color:indigo;">15</td>
</tr></table></div>

<p>would zigzag into the following formation</p>
<div class="flex-container"><div class="container-item"><table class="map"><tr>
<td style="background-color:darkgreen;">0</td>
<td style="background-color:darkblue">1</td>
<td style="background-color:darkblue">5</td>
<td style="background-color:purple;">6</td></tr><tr>
<td style="background-color:purple;">2</td>
<td style="background-color:darkgreen">4</td>
<td style="background-color:indigo">7</td>
<td style="background-color:darkgreen;">12</td></tr><tr>
<td style="background-color:indigo;">3</td>
<td style="background-color:darkgreen">8</td>
<td style="background-color:indigo">11</td>
<td style="background-color:darkblue;">13</td></tr><tr>
<td style="background-color:darkblue;">9</td>
<td style="background-color:purple">10</td>
<td style="background-color:purple">14</td>
<td style="background-color:indigo;">15</td></tr></table></div>

<div class="spacer"><span class="b lg">or</span></div><div class="container-item">
<img class="smallpic" src="../static/images/05/lineb.png"/></div></div>""",
                        instructions='Your extruded wire (same as Part 1):',
                        input_type='png',
                        form='<label class="main" for="answer2">\n How many liters of diamond gas were harvested?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  958013\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=6,
                        sub_entry_id=1,
                        title='Here Comes a Sun',
                        content="""<p>Today's assignment is in the
<a href="https://en.wikipedia.org/wiki/Thermal_management_(electronics)">Thermal
Defense </a>Room. This room serves as the ship's primary defense against the
unforgiving natural perils of space — extreme heat and harmful
<a href="https://en.wikipedia.org/wiki/Radiation">radiation</a>.</p>

<p>In space, the ship is constantly bombarded with <span class="b i"> waves of different
frequencies and wavelengths</span>. Some of these waves, called <span class="b i">
Solar Waves, are damaging</span> to the structure of the ship, while others, called
<span class="b i">Cosmic Waves, are harmless</span>.</p>

<p>The ship has a Thermal Defense System in place, but it works best when
it is specifically targeted at harmful Solar Waves.</p>

<p>A <a href="https://en.wikipedia.org/wiki/Comma-separated_values">comma-separated</a>
database is already on file, containing the individual frequencies and wavelengths of
previously intercepted waves. However, <span class="b i">some incoming waves have a
combination of frequency and wavelength that has not yet been classified</span>.</p>

<p>Your job is to <span class="b i">determine if these waves are harmful</span> Solar
Waves or harmless Cosmic Waves. To do so, you need to find <span class="b i">the 7
known waves</span> from the database <span  class="b i">that are nearest to the unknown
wave</span>.</p>

<p>The distance between waves is determined by graphing the coordinates, with
<span class="b i">frequency representing the x-axis</span> and <span class="b i">
wavelength representing the y-axis</span>.</p>

<div class="imgcontainer"><img class="pad" src="../static/images/06/euclidian1.png"/>
</div>The <span class="b i">
<a href="https://en.wikipedia.org/wiki/Euclidean_distance">Euclidean Distance Formula
</a></span>(above) is then used to gauge how near or far one point is from another. The
<span class="b i">majority type among the 7 closest neighbors</span> of a new wave will
determine whether that new wave is a Solar Wave or a Cosmic Wave.

<p>The data provided, your puzzle input, begins with a <span class="b i">single line of
new waves</span>, with each wave represented by its frequency and wavelength separated
by a comma; the <span class="b i">individual waves are separated by spaces</span>.
Following this line are <span class="b i"> several lines in a comma-separated 
format</span>, providing a <span class="b i">database of known waves</span>. In this
format, the first column is "frequency", the second column is "wavelength", and the
third column is "type". Determine whether each new wave is a Solar Wave
(<span class="b i">S</span>) or a Cosmic Wave (<span class="b i">C</span>), and 
concatenate these results without spaces into an <span class="b i"> uppercase 
five-character output</span>.</p>

<h4>For example:</h4>

<p>Your unknown waves are <span class="code part">(9,2) (6,4) (3,5)</span><br/> and
your database consists of<span class="code free">
  frequency,wavelength,type<br/>
  10,7,Cosmic<br/>
  9,1,Solar<br/>
  7,2,Solar<br/>
  8,3,Cosmic<br/>
  10,2,Solar<br/>
  9,3,Solar<br/>
  1,5,Cosmic<br/>
  4,5,Cosmic<br/>
  9,4,Solar<br/>
  3,3,Solar</span></p>

<p>
To find the distance from the first unknown wave (9,2) to the first wave in the database
(10,7), you would apply the Euclidean Distance Formula, taking the sum of the difference
of the Xs squared and the difference of the Ys squared:<br/><span class="code part">
√( (10-9)² + (7-2)² )  =  √( 1² + 5² )  =  √( 1 + 25 )  =<br/>√( 26 )  =  5.099</span></p>

<p>So the distance between the first unknown target wave and the known Cosmic Wave at
(10,7) is <span class="code part">5.099</span></p>

<p>Applying this formula to every wave in the database you get:<span class="code free">
frequency,wavelength,type,<span class="b">distance</span><br/>
10,7,Cosmic,<span class="b">5.099</span><br/>
9,1,Solar,<span class="b">1.000</span><br/>
7,2,Solar,<span class="b">2.000</span><br/>
8,3,Cosmic,<span class="b">1.414</span><br/>
10,2,Solar,<span class="b">1.000</span><br/>
9,3,Solar,<span class="b">1.000</span><br/>
1,5,Cosmic,<span class="b">8.544</span><br/>
4,5,Cosmic,<span class="b">5.830</span><br/>
9,4,Solar,<span class="b">2.000</span><br/>
3,3,Solar,<span class="b">6.082</span></span>

Since you have such a small amount of data in this example, let's only look at the
<span class="b i">3 nearest neighbors</span>. Those would be
<ol><li>
  Solar Wave at (9,1)
</li><li>
  Solar Wave at (10,2)
</li><li>
  Solar Wave at (9,3)
</li></ol>

Majority wins (and in this case all neighbors are the same type) so the unknown wave at 
(9,2) is Solar, or <span class="code part">S</span>.</p>

<p>Repeating the same process for all the unknown waves, you get
<ol><li>
  for (9,2): Solar, Solar, Solar = <span class="b i">S</span>
</li><li>
  for (6,4): Cosmic, Cosmic, Solar = <span class="b i">C</span>
</li><li>
  for (3,5): Cosmic, Cosmic, Solar = <span class="b i">C</span>
</li></ol>
  So our uppercase output would be<span class="code part">SCC</span></p>""",
                        instructions='Here is your data...',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n What is the five-character output?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  SSCSC\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=6,
                        sub_entry_id=2,
                        title='Missing Mystery Part',
                        content="""<p>You have successfully isolated some harmful Solar Waves and are ready to
<span class="b i">direct the Thermal Defense System at them</span>, but the diagnostic
panel indicates a <span class="b i">critical malfunction</span>. This malfunction has
prevented the system from repairing itself or identifying the broken part.</p>

<p>The entire Thermal Defense System comprises <span class="b i">multiple types of
<a href="https://www.merriam-webster.com/dictionary/bespoke">bespoke</a> parts</span>,
each designed for different levels of radiation protection and thermal management.
Because many different parts share similar qualities, it is difficult to determine
the exact replacement needed.</p>

<p>In the parts storage, you <span class="b i">find a replacement part</span> that
matches some of the specifications of the broken component. However, the specifications
alone — <span class="b i">mass, density, thickness, area, and radiation output</span>
 — are insufficient to confirm the exact component required. This is because various
parts have similar physical characteristics but different performance metrics and
configurations.</p>

<p>To identify the unknown part, you'll need to <span class="b i">compare it to all
parts in the database</span> by measuring similarity across multiple dimensions. You
can gauge this similarity <span class="b i">using Euclidean distance</span> — the
smaller the distance, the more similar the parts. However, since there are
<span class="b i">more than two dimensions</span> to each part, you need to use a more
robust equation with <span class="code part">q</span> representing the target's value and
<span class="code part">p</span> representing the value from the database you are
comparing it to. with Σ representing the aggregate squared differences of each dimension
from 1 to n.</p>

<div class="imgcontainer">
<img class="midpic" src="../static/images/06/euclidian2.png"/></div>

<p>Just as you did when sorting the waves, you need to look at <span class="b i">the 7
Thermal Defense System parts nearest to the mystery part</span>. Then you can determine
its purpose based on the majority of its <span class="b i">nearest neighbors</span>.</p>

<p>Your data consists of a first line, the specifications of the mystery part, separated
by commas, followed by the database of known parts, similarly comma-separated, with
columns for mass, density, thickness, area, radiation output, and type.</p>

<h4>For example:</h4>

<p>If your mystery part, the target (<span class="b i">q</span>), has the values
<span class="code free">mass,density,thickness,area,radiation_output<br/>
12.5,31.22,3.402,2.0,0.053</span> and you want to find its distance compared to this
"<span class="b i">Boron\xa0Nitride\xa0Nanotube\xa0Composite</span>" part in the 
database (<span class="b i">p</span>)<span class="code free">
mass,density,thickness,area,radiation_output<br/>15.9,10.6,4.47,2.79,0.451</span></p>

<p>Following the Euclidean distance formula above, you need the square root of the sum 
of all the following differences squared.
<ol><li>mass</li><ul><li><span class="code part">(12.5 - 15.9)² = 11.56</span></li></ul>
<li>density</li><ul><li><span class="code part">(31.22 - 10.6)² = 425.1844</span></li></ul>
<li>thickness</li><ul><li><span class="code part">(3.402 - 4.47)² = 1.1406</span></li></ul>
<li>area</li><ul><li><span class="code part">(2.0 - 2.79)² = 0.6241</span></li></ul>
<li>radiation output</li><ul><li><span class="code part">(0.053 - 0.451)² = 0.1584</span>
</li></ul></ol></p>

<p>You take the square root of the sum of these differences <span class="code part">
√( 11.56 + 425.1844 + 1.1406 + 0.6241 + 0.1584 ) =<br/>√( 438.6675 )  =  20.9443</span></p>

<p>The distance between the mystery part in the example and the one
Boron\xa0Nitride\xa0Nanotube\xa0Composite part is <span class="code part">
20.9443</span>.</p>

<p>The following process is the same as you did in Part 1, finding the
<span class="b i">7 nearest neighbors</span> of your mystery part to determine its type.</p>""",
                        instructions='Here is your data...',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n What is the mystery part?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  ZIRCONIUM DIOXIDE CERAMIC HEAT SINK\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=7,
                        sub_entry_id=1,
                        title='Pharma-geddon',
                        content="""<p>After a few days of high-tension work in other areas of the ship, you put in a request
for a more laid-back task. Helping to organize the inventory in the
<a href="https://en.wikipedia.org/wiki/Sick_bay">Sick Bay</a> sounds like a great,
mindless task that you can relax by doing.</p>

<p>As seems to be your usual misfortune, you arrive to yet another tableau of stress and
confusion. The medical officer has just put in <span class="b i">an order for some
medical supplies</span>, but someone has lost the reference sheet for the inventory.
Without the <span class="b i">four-symbol code</span> for each item, you cannot retrieve
it from the <a href="https://en.wikipedia.org/wiki/Vending_machine">auto-vending
storage</a>.</p>

<p>The only files that are found are <span class="b i">an inventory, listing the name and
quantity of each supply</span>, and <span class="b i">a raw data file, your input puzzle,
that stores the entire <a href="https://docs.python.org/3/library/collections.html">
collections</a> of medical supplies</span>. As these items were entered into the ship's
inventory in no particular order, their four-symbol codes were
<a href="https://en.wikipedia.org/wiki/Concatenation">concatenated</a> onto the raw data
file<span class="b i"> with no separator</span>.</p>

<p>You are asked if you know of any
<a href="https://docs.python.org/3/library/collections.html#collections.Counter">
Counter</a> that can process this raw data file and <span class="b i">tell you the number
of appearances of all the four-symbol codes</span>. Then you can cross-check it with
the plain text inventory.</p>

<p>Using the raw data file, <span class="b i">find each four-symbol code that appears the
number of times corresponding to each item's quantity</span>. Print these codes
<span class="b i">next to each other without any spaces</span> to retrieve them from
the storage.</p>

<h4>For example:</h4>

<p>If your raw data file looks like <span class="code" style="word-break: break-all;">
**_#@$%&amp;()[]#?!)()[]#?!)()[]()[]@$%&amp;@$%&amp;()[]()[]()[]()[]@$%&amp;@$%&amp;#?!)**_#**_#@$%&amp;#?!)
</span> We can see
<ul><li>8 occurrences of  <span class="code part">()[]</span></li>
<li>6 occurrences of <span class="code part">@$%&amp;</span></li>
<li>4 occurrences of <span class="code part">#?!)</span></li>
<li>3 occurrences of <span class="code part">**_#</span></li></ul></p>

<p>If the plain text inventory tells you there are 8 hypodermic needles and 4 plaster
casts, You can determine from your count that the four-symbol code for hypodermic needles
is <span class="code part">()[]</span> and the four-symbol code for plaster casts is
<span class="code part">#?!)</span>.</p>

<p>To get these items from the storage, you will input<span class="code part">
()[]#?!)</span>.</p>""",
                        instructions='The medical officer has requested bandages,\n    healing serum, and antacids.\n<p class="main">\n Plain text inventory:\n <span class="code free main">\n  •\n  <span class="b i main">\n   1081\n  </span>\n  packages of standard adhesive bandages\n  <br/>\n  •\n  <span class="b i main">\n   1055\n  </span>\n  vials of\n    "InstaHeal" disinfectant and wound\n    closure serum\n  <br/>\n  •\n  <span class="b i main">\n   965\n  </span>\n  blister packs\n    of "Yucky Tummy No More" chewable antacids\n </span>\n Raw data file:\n</p>',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n What is the code to retrieve these three items?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  &lt;({%=!+`&lt;%{&gt;\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=7,
                        sub_entry_id=2,
                        title='Have a Proper Gander',
                        content="""<p>With that crisis averted, the rest of your day goes by pretty smoothly as you help
your shipmates reorganize the inventory. Suddenly, out of the corner of your eye, you
<span class="b i">spot a colorful piece of paper</span>.</p>

<div class="imgcontainer">
<img class="fill" src="../static/images/07/propoganda.png"/></div>

<p>Picking it up, you immediately recognize it as <span class="b i">Aurawrought
<a href="https://en.wikipedia.org/wiki/Propaganda">propaganda</a></span> that someone
aboard the ship must have sneaked in. The Aurawrought race are eerie luminous entities
from The Veil of First Light, a shifting nebula at the edge of known space where time
bends strangely. You've learned in your orientation, prior to boarding the ship, that
their once-unassuming movements have grown calculated, their murmurs in the cosmic dark
turning into proclamations. This mission you're on, with the crew of STS Solara, is to 
investigate and likely stop what they are planning.</p>

<p>Could there be a <a href="https://en.wikipedia.org/wiki/Treason">traitor</a> amongst
us who has brought this paper on board?</p>

<p>Call it a <a href="https://en.wikipedia.org/wiki/Intuition">hunch</a>, but you 
notice something very strange about the <span class="b i">colors of the eyes</span>
on the page. It looks like someone has colored them in. Luckily, there is a
<span class="b i">Propaganda Inspecting LumiCam (PIL)</span> app built into your
holographic tablet, designed to <span class="b i">scan images for color</span>.</p>

<p>To uncover the <span class="b i">hidden message</span>, you need to program it to
act as a
<a href="https://docs.python.org/3/library/collections.html#collections.Counter">
Counter</a> for each pixel color you scan. You decide on a quick course of action.</p>

<div class="shadow pad"><ol><li>Scan the Image</li><ul><li>
  Use your PIL app to scan the strange colors from the eyes of the image (your puzzle
  input)
</li></ul><li>Count the Colors</li><ul><li>
  The app should count each color pixel and provide you with a list of RGB tuples for
  the top three most frequent colors in descending order 
</li></ul><li>Convert Hex Values</li><ul><li>
  Convert the RGB tuples to <a href="https://www.color-hex.com/">hex color values</a>
  and then change all of the digits to their closest uppercase letter using the 
  following mapping:<br/>
  <span class="b i">0=O, 1=I, 2=Z, 3=E, 4=A, 5=S, 6=G, 7=T, 8=B, and 9=P</span>
</li></ul></ol></div>

<p>The resulting <span class="b i">six-letter words from the top three hex color values
</span> will reveal the secret message hidden inside the propaganda paper.</p>

<h4>For example:</h4>
<p>Using this image below,</p>
<div class="imgcontainer"><img class="midpic" src="../static/images/07/sample.png"/></div>

<p>We get the following counts for pixel colors: <span class="code free">
(255, 255, 255): 2180<br/>
(\xa0\xa00, \xa0\xa00, \xa0\xa00): 1917<br/>
(176, 209, 229): 10002<br/>
(190, 173, 237): 10001<br/>
(222, 202, 222): 10000</span></p>

<div class="flex-container"><div class="container-item pad">Converting the top 3<br/>
colors to hex values<span class="code free">
#B0D1E5<br/>
#BEADED<br/>
#DECADE</span></div>

<div class="container-item pad">and changing the digits<br/>to uppercase letters
<span class="code free">
BODIES<br/>
BEADED<br/>
DECADE</span></div></div>

<p>The secret message becomes <span class="code part">BODIES BEADED DECADE</span>.</p>""",
                        instructions='Here is a section of just the eye colors from the propaganda paper:',
                        input_type='png',
                        form='<label class="main" for="answer2">\n What is the secret message?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  ACCESS OFFICE COFFEE\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=8,
                        sub_entry_id=1,
                        title='Full of Beans',
                        content="""<p>That was an odd message. What could it mean? The only place aboard the ship to get a
cup of coffee is the coffee machine in the Crew Quarters' common room. No one's around
so you put the propaganda paper down on the table and start to make a cup of coffee for
yourself.</p>

<p>Suddenly, you hear a small high-pitched voice behind you. Out of the corner of your
eye, you see what looks like a small Aurawrought being, about 20cm tall.</p>

<div class="imgcontainer">
<img class="smallpic" src="../static/images/08/defector.png"/></div>

<p>You whip around, keeping an eye out for some sort of weapon you can use, all while
trying not to break eye contact with the creature. Sensing your distress, it quickly
tells you that it has come in peace, explaining further that it is a
<a href="https://en.wikipedia.org/wiki/Defection">defector</a> from the Aurawrought
army. It left the propaganda on the ship in hopes someone would find it and get in
touch, because it has important information to share.</p>

<p>The Aurawrought have long devoted themselves to Eos, goddess of the dawn, and have
lamented her imprisonment in the galactic vortex where she has been held for centuries.
Recently, however, the scientists among the Aurawrought have come up with a means to
free her. This defector insists that it does not share the zealotry of its fellow
Aurawroughts and seeks your help to stop its brethren from unleashing a dangerous deity
into the universe. You are skeptical, but something in its demeanor convinces you to
trust it. The tiny defector says it needs to prepare some documents for you —
<span class="b i">a map</span> to travel directly to the Aurawroughts, avoiding their
army's entire fleet, and <span class="b i">the blueprints of the technology</span> they
are planning to use to free Eos. It promises to be in touch soon and asks you to wait
for it to return with the paperwork.</p><hr/>

<p>In the meantime, you look around at the state of the common area. A new shipment of
coffee beans had arrived just in time, as there was nothing left from the old shipment
besides the handful of beans inside the machine. All the bags of coffee beans are inside
a <a href="https://en.wikipedia.org/wiki/Knapsack_problem">knapsack</a>, waiting to be
shelved. To kill time, you decide to take some initiative and <span class="b i">
stock some coffee</span>.</p>

<p>There are <span class="b i">100 bags of coffee beans in varying sizes</span> from all
over Earth, and they will not all fit on the shelf. You scan the inventory list on your
holographic tablet, which displays a comma-separated document detailing the shipment:
<span class="b i">country, bean type, roast, width of the bag, and popularity rating
</span> — your puzzle input. You should:</p>

<ol><li><span class="b i">Consider an Individual Coffee Bag:</span>
</li><ul>
  Define a way to group together the country, bean type, roast, width, and
  popularity rating for each coffee bag.
</ul><li><span class="b i">Create a Plan to Organize the Shelf:</span>
</li><ul>
  Consider a shelf an object that can <span class="b i"> hold a certain number of coffee
  bags</span>, remembering it has a fixed width capacity.
</ul><li><span class="b i">Stock the Shelf Efficiently:</span>
</li><ul>
  Implement a method to store the coffee bags on the shelf with <span class="b i"> the
  best possible popularity rating while minimizing wasted space</span>.
</ul></ol>

<p>By organizing the coffee bags this way, you can ensure that the shelf is stocked with
the best selection for the crew.</p>

<h4>For example, look at a small shelf of<span class="code part">70</span>cm:</h4>

<p>If you have the following inventory<span class="code free">
country,bean,roast,width,rating<br/>
Jamaica,Arabica,Light Roast,40,5<br/>
Brazil,Robusta,French Roast,20,3<br/>
Columbia,Typica,French Roast,30,4<br/>
Uganda,Arabica,Vienna Roast,10,2<br/>
Mexico,MundoNovo,Cinnamon Roast,30,2</span>
To minimize wasted space you should fill the shelf with coffee bags totaling as close
to 70cm as possible.</p>

<p>Several combinations are possible: Choosing the coffees from <span class="b i">
Jamaica and Columbia</span> total 70cm, as does combining <span class="b i">Jamaica and
Mexico</span>. Smaller bags can also reach 70m, such as those from <span class="b i">
Columbia, Uganda, and Mexico</span>. It is also possible to obtain a high popularity
rating while coming up slightly short of 70cm, like with <span class="b i">Brazil,
Columbia, and Uganda</span>, which total 60cm. With so many options, the goal is to
<span class="b i">select the combination that yields the highest total popularity
rating</span>.</p>

<div class="imgcontainer">

<table><tr><th>Coffee Bags</th><th>Total Width</th><th>Total Rating</th></tr>
<tbody class="P2"><tr><td>Jamaica+Columbia</td><td>70</td><td>9</td></tr>
<tr><td>Jamaica+Mexico</td><td>70</td><td>7</td></tr>
<tr><td>Columbia+Uganda+Mexico</td><td>70</td><td>8</td></tr>
<tr><td>Jamaica+Brazil</td><td>60</td><td>8</td></tr>
<tr><td>Brazil+Uganda+Mexico</td><td>60</td><td>7</td></tr>
<tr><td class="select">Jamaica+Brazil+Uganda</td>
<td class="select">70</td><td class="select">10</td></tr>
<tr><td>Brazil+Columbia+Uganda</td><td>60</td><td>9</td></tr>
<tr><td>Columbia+Mexico</td><td>60</td><td>6</td></tr></tbody></table></div>

<p>Although several combinations fill the shelf close to 70cm, the combination of
<span class="b i">Jamaica Arabica Light Roast, Brazil Robusta Dark Roast, Uganda Arabica
French Roast</span> have the best total popularity rating of <span class="code part">
10</span>.</p>""",
                        instructions='Your shelf is\n<span class="main code part">\n 500\n</span>\ncm wide.\n<br/>\nHere is the inventory of all the coffee beans:',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n What is the total popularity rating?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  653\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=8,
                        sub_entry_id=2,
                        title='Bean Around the World',
                        content="""<p>After finishing stocking one shelf, you look around for the Aurawrought defector.
Come to think of it, it didn't specify how soon it would be back, if at all today. You
still have some time to kill before calling it a night, so you decide to
<span class="b i">stock the rest of the shelves</span>.</p>

<p>Looking over the stocking job you just completed, you realize that <span class="b i">
you could put even more effort into assuring a wide variety</span> of coffee bags on the
shelves. You decide to further constrain your selections so there are <span class="b i">
no duplicate bean types and no duplicate roasts</span> on each shelf. This might decrease
the overall popularity rating, but it will ensure that there is a more varied selection
for the crew.</p>

<p>This ship seems to have been built on a tight budget, as the three available
<span class="b i">shelves are all different lengths</span>. Keeping in mind your new
restrictions about bean types and roasts for each shelf, <span class="b i">restock all
three shelves</span>.</p>

<p>Once the three shelves are stocked, you can return to your bunk to sleep.</p>

<h4>For example:</h4>

<p>Using the same shelf and inventory from Part 1's example, the answer you arrived at is
no longer the best because there is not enough variation. <span class="b i">There are two
bags of Arabica beans</span> on the shelf. <span class="b i">Removing combinations where
there are duplicate bean types, or duplicate roasts</span> gives you fewer coffee bag
combinations to consider.</p>

<div class="imgcontainer"><table>
<tr><th>Coffee Bags</th><th>Total Width</th><th>Total Rating</th>
<th>Reason Removed</th></tr><tbody class="P2">
<tr><td class="select">Jamaica+Columbia</td><td class="select">70</td>
<td class="select">9</td><td></td></tr>
<tr><td>Jamaica+Mexico</td><td>70</td><td>7</td><td></td></tr>
<tr><td>Columbia+Uganda+Mexico</td><td>70</td><td>8</td><td></td></tr>
<tr><td>Jamaica+Brazil</td><td>60</td><td>8</td><td></td></tr>
<tr><td>Brazil+Uganda+Mexico</td><td>60</td><td>7</td><td></td></tr>
<tr><td class="cross">Jamaica+Brazil+Uganda</td><td class="cross">70</td>
<td class="cross">10</td><td>Same Bean</td></tr>
<tr><td class="cross">Brazil+Columbia+Uganda</td><td class="cross">60</td>
<td class="cross">9</td><td>Same Roast</td></tr>
<tr><td>Columbia+Mexico</td><td>60</td><td>6</td><td></td></tr></tbody></table></div>

<p>Repeat the process of filling a shelf with coffee bags of varying bean types and
roasts for all three shelves. You cannot use the same bag on more than one shelf, but
there's no need to consider the bean types and roasts of other shelves.
<span class="b i">Restrictions on bean type and roast apply only within each shelf</span>,
not across all shelves.</p>""",
                        instructions='Your three shelves are\n<span class="main code part">\n 500, 415, 495\n</span>\ncm wide.\n<br/>\nHere is the inventory of all the coffee beans\n<br/>\n<span class="main sm">\n (same input as Part 1)\n</span>\n:',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n What is the sum of the popularity ratings for all shelves?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  1625\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=9,
                        sub_entry_id=1,
                        title='Get Us Outta Here',
                        content="""<p>You wake up to find the Aurawrought defector standing far too close to your face,
staring at you intently. Startled, you nearly leap to the opposite end of your bunk.
Clearly, these beings are not familiar with the concepts of privacy or
<a href="https://en.wikipedia.org/wiki/Proxemics">personal space</a>. It proudly
announces that it's finished with the <span class="b i">map to the Aurawroughts</span>
and hands you a piece of paper, your puzzle input. However, instead of containing any
legible coordinates or paths, it has <span class="b i">a list of
<a href="https://en.wikipedia.org/wiki/Node_(computer_science)">nodes</a> and their
connections</span>.</p>

<p>The defector explains that the path to the Aurawroughts must first cross a
<a href="https://en.wikipedia.org/wiki/Nebula">Nebula</a>
<a href="https://en.wikipedia.org/wiki/Labyrinth">Labyrinth</a>, riddled with
electromagnetic storms. <span class="b i">The node system reveals the paths that avoid
the storms</span>, guiding the ship safely outside the Nebula Labyrinth.</p>

<p>You realize you need to take this information to Captain Xarlos on the
<a href="https://en.wikipedia.org/wiki/Bridge_(nautical)">Bridge</a>, but first, you
must make sense of this strange system. Your task is to scour the <span class="b i lg">
depths</span> of the Nebula Labyrinth and find <span class="b i"> the safest path
through the storms</span>.</p>

<p>Your paper contains</p>
<ul><li><span class="b i">First Line</span></li><ul><li>
  The <span class="b i">starting node and ending node</span>, separated by a comma.
</li><li>
  This represents the ship's current location and the exit of the Nebula Labyrinth.
</li></ul><li class="pad"><span class="b i">Subsequent Lines</span></li><ul><li>
  All the <span class="b i"> nodes and their connections, separated by colons</span>.
  <br/>(node:connection)
</li><li>
  Each node-connection combination is on its own line.
</li><li>
  If a node has <span class="b i"> multiple connections</span>, those connections are
  <span class="b i">separated by commas</span>.
</li></ul></ul>

<p>You can guide Captain Xarlos through the shortest path, but he first would like to
know <span class="b i">how many units of space must be traversed</span>.<br/>
<span class="sm">(Each node represents one unit of space.)</span></p>

<h4>For example:</h4>

<div class="flex-container"><div class="container-item">
Consider this data<span class="code free">
10,31<br/>
10:18<br/>
12:13,20<br/>
13:12,14<br/>
14:13,15,22<br/>
15:14<br/>
18:10,26<br/>
20:12,28<br/>
22:14,30<br/>
26:18,27<br/>
27:26,28<br/>
28:27,29<br/>
29:28,30<br/>
30:22,29,31<br/>
31:30</span></div>

<div class="column"><div class="column-content">You see in the first line that the
starting node is <span class="code part">10</span> and the ending node is
<span class="code part">31</span>.</div>
<div class="spacer"></div>

<div class="column-content">If it helps to visualize this as a 2D maze, it would look
like this</div>
<div class="spacer"></div>

<div class="column-content"><table class="map">
<tr><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td></tr>
<tr><td>#</td><td class="o">10</td><td>#</td><td class="o">12</td><td class="o">13</td>
<td class="o">14</td><td class="o">15</td><td>#</td></tr>
<tr><td>#</td><td class="o">18</td><td>#</td><td class="o">20</td><td>#</td>
<td class="o">22</td><td>#</td><td>#</td></tr>
<tr><td>#</td><td class="o">26</td><td class="o">27</td><td class="o">28</td>
<td class="o">29</td><td class="o">30</td><td class="o">31</td><td>#</td></tr>
<tr><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td></tr>
</table></div></div></div>

<p>Following the nodes' connections, you can take different paths:
<ul><li>
  10-18-26-27-28-20-12-13-14-22-30-31 : 12 units of space
</li><li>
  10-18-26-27-28-29-30-31 : 8 units of space
</li></ul>
  The shortest path through this map is <span class="code part">8</span> units of space
  long.</p>

<div class="imgcontainer"><table class="map">
<tr><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td></tr>
<tr><td>#</td><td class="select">10</td><td>#</td><td class="o">12</td>
<td class="o">13</td><td class="o">14</td><td class="o">15</td><td>#</td></tr>
<tr><td>#</td><td class="select">18</td><td>#</td><td class="o">20</td><td>#</td>
<td class="o">22</td><td>#</td><td>#</td></tr>
<tr><td>#</td><td class="select">26</td><td class="select">27</td><td class="select">28</td>
<td class="select">29</td><td class="select">30</td><td class="select">31</td><td>#</td></tr>
<tr><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td><td>#</td></tr>
</table></div>

<p>Now, it's time to navigate the actual map through the Nebula Labyrinth.</p>""",
                        instructions='Here is your data for the starting point, ending point, and nodes:',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n How many units of space does the shortest path traverse?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  289\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=9,
                        sub_entry_id=2,
                        title='Wormholey Moley!',
                        content="""<p>At the Bridge, Captain Xarlos is delighted to have a map to the Aurawroughts. Together,
you expertly navigate the ship through the electromagnetic storms, following your path.
Once through the Nebula Labyrinth, you find yourselves in a <span class="b i">clearing of
open space</span>. There's no sign of the Aurawroughts in sight, so there must be
<span class="b i">more to the route ahead</span>, but what?</p>

<p>Just then, you see Captain Xarlos' face
<a href="https://dictionary.cambridge.org/dictionary/english/as-white-as-a-sheet">
turn white</a>, his hand ready on his <a href="https://en.wikipedia.org/wiki/Raygun">
space blaster</a>, staring just above your left shoulder. You instantly know it must be
the tiny defector, but you turn to look anyway while trying to reassure the captain that
everything is fine. Captain Xarlos is skeptical but ultimately trusts you and relaxes a
bit as you explain the creature.</p>

<p>It turns out, <span class="b i">the small defector has forgotten to give you the other
half of the directions to the Aurawroughts</span>. It gives you <span class="b i">
another sheet of nodes</span>, in the same format as before. This time, there are no
storms blocking your path, but instead, a <span class="b i">vast open space guarded by
the Aurawrought <a href="https://en.wikipedia.org/wiki/Stealth_technology">stealth
army</a></span>. The nodes represent paths on the map that are outside of the
<a href="https://en.wikipedia.org/wiki/Line_of_sight">line of sight</a> of those enemy
ships.</p>

<p>You will need to <span class="b i">travel through
<a href="https://en.wikipedia.org/wiki/Wormhole">wormholes</a></span> to reach the heart
of the Aurawrought's operations. The issue is that <span class="b i"> each wormhole can
connect to a great many other nodes</span>, reflected on your puzzle input, and choosing
<span class="b i">the wrong node to travel to could add hours or even days to your
journey</span>. Following every path from a wormhole will not be the most efficient route.
It's clear that scouring the depths of space won't work. Instead, consider examining the
<span class="b i lg">breath</span> of space for a more effective strategy.</p>

<p>For this mission as well, Captain Xarlos must determine <span class="b i">how many
units of space will be traversed</span>. Help devise a plan so you and Captain Xarlos
can navigate your way, avoiding detection.</p>

<h4>For example:</h4>

<p>You will recognize wormholes on your document by the large number of connections that
the node has. While most nodes connect to just a few other nodes (usually up, down, left,
or right if you think of it as a 2D grid), wormholes connect to many more.
<span class="code free">297:197,1209,1573,1733,2127,3168,3176,3184,3252,3754,3758, …
</span> Apart from that, units of space are measured exactly the same as before with the
wormhole node counting as one unit, and the connection you choose to follow counting
as another.</p>""",
                        instructions='Here is your data with the starting point, ending point, and nodes:',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n How many units of space does the shortest path traverse?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  424\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=10,
                        sub_entry_id=1,
                        title='All Hands on Deck',
                        content="""<p>You've navigated through the wormhole and arrived just outside of the Aurawroughts'
<a href="https://www.dictionary.com/browse/headquarters">secret base</a>, successfully
avoiding detection by enemy ships. <span class="b i">Captain Xarlos calls
<a href="https://www.dictionary.com/browse/all-hands-on-deck">all hands to the Main
Deck</a></span>. The ship's <a href="https://en.wikipedia.org/wiki/Laser">high-powered
laser</a> needs to be manned for the upcoming attack, and your assistance is needed to 
coordinate the crew's route to the deck.</p>

<p><span class="b i">The hallways leading to the Main Deck have different
capacities</span>, allowing varying numbers of crew members to pass through
simultaneously.</p>

<p><span class="b i">Starting from the source, Storage Room 1 (S1)</span>, the crew must
<span class="b i">choose their paths through the hallways</span>, passing other storage
rooms or junctions, <span class="b i"> to reach the destination, the Main Deck
(MD)</span>. Captain Xarlos emphasizes the need for fast, efficient movement and
<span class="b i">requests a calculation of the
<a href="https://en.wikipedia.org/wiki/Ford%E2%80%93Fulkerson_algorithm">
maximum flow</a></span> — the greatest number of crew members that can move through the
hallways at one time.</p>

<p>You quickly annotate <span class="b i">the floor plan</span> on your holographic
tablet, <span class="b i">listing each hallway as a pair of connected rooms separated by
a hyphen, followed by a space and the hallway's capacity</span> — this serves as your
puzzle input.</p>

<p>It's crucial that no crew members linger in any room or hallway, as this would
restrict the flow. The entire crew that <span class="b i">starts from the source (S1)
must travel to the destination (MD) and arrive together</span>. Captain Xarlos awaits your
calculation of the maximum number of crew members that can flow through the hallways
simultaneously so he can efficiently instruct his sizable crew.</p>

<h4>For example:</h4>

<p>With your source at <span class="code part">A</span>, your destination at
<span class="code part">F</span>, and a floor plan like <span class="code free">
A-B 3<br/>
A-C 3<br/>
B-C 2<br/>
B-D 3<br/>
C-E 2<br/>
D-E 4<br/>
D-F 2<br/>
E-F 3</span>
Your task is to find the paths that result in <span class="b i">getting the most possible
crew members to the destination, given the hallways' capacity restrictions</span>.</p>

<div class="imgcontainer">
<img class="fill" src="../static/images/10/example.gif"/></div>

<p>Demonstrated in the animation above, you can see the best paths to achieve the
maximum possible flow from the source to the destination.</p>

<p>Identifying the most efficient path selection allows you to determine that the maximum
flow for this floor plan is <span class="code part">5</span>.</p>""",
                        instructions='Your source is\n<span class="code part main">\n S1\n</span>\nand your destination is\n<span class="code part main">\n MD\n</span>\n<br/>\nHere is your floor plan:',
                        input_type='txt',
                        form='<label class="main" for="answer1">\n What is the maximum flow?\n <br/>\n</label>\n<input autocomplete="off" name="answer1" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  418\n </span>\n .\n</label>',
                    ),
                    SubEntry(
                        main_entry_id=10,
                        sub_entry_id=2,
                        title='Through the Cracks',
                        content="""<p>The crew is in place and ready to commence. In the distance, you can see the
technology that the Aurawroughts intend to use to free Eos from her galactic prison,
safeguarded within a protective dome.</p>

<div class="imgcontainer">
<img class="midpic" src="../static/images/10/orb.png"/></div>

<p>Suddenly, the tiny defector materializes again, seemingly out of nowhere, holding a
large rolled sheet of paper. It explains that these are the
<a href="https://en.wikipedia.org/wiki/Blueprint"><span class="b i">blueprints</span></a>
for the protective dome</p>

<p>The inner technology is delicate and can quite easily be destroyed with a blast from a
laser, but the dome is much stronger. According to the blueprint, this dome is a
<span class="b i">lattice of interconnecting nodes, each with specific pathways for energy
flow</span>. There is only <span class="b i">one viable point of attack — Node 0</span>.</p>

<div class="imgcontainer"><a href="../static/images/10/blueprint.png">
<img class="fill" src="../static/images/10/blueprint.png"/></a></div>

<p>Any laster blast targeting elsewhere on the shield will be deflected. However, when
struck at Node 0, <span class="b i">the dome is designed to disperse the incoming energy
across all its connected edges</span>. Each interconnecting node has a direction and a
capacity for the amount of energy it can transmit.</p>

<p>To successfully penetrate the dome and destroy the technology inside, you must first
<span class="b i">deliver a precise blast of energy from the laser</span>. Sending
<span class="b i">too little energy will dissipate</span> across the edges and weaken the
blast, while sending <span class="b i">too much will cause an overload</span> if the
capacity of any edge is exceeded with no alternative paths available to handle the
overflow. Your task is to calculate the <span class="b i">maximum flow from the source
(Node 0) to all 5 destinations (Nodes 76, 77, 78, 79, and 80) combined</span>.</p>

<p class="hint-label ssm">HINT (mouse-over to view):</p>
<p class="hint ssm">Maximum flow algorithms work when there is only 1 destination. How
would you connect these 5 destinations into one final imaginary destination to aggregate 
the maximum flow from all areas of the dome, and what should you consider for the
capacity for these imaginary edges?</p>

<p>The tiny defector has also provided you with a <span class="b i">list of capacities
for each edge</span>, your puzzle input, formatted similarly to your previous floor plan
annotations. Connecting nodes are separated by hyphens, followed by a space and the
capacity for that edge. <span class="b i">A listed capacity of "Inf" indicates infinite
capacity, meaning there is no limitation on the energy that can flow between those two 
nodes</span>.</p>""",
                        instructions='Your source is\n<span class="code part main">\n S1\n</span>\nand your destinations are\n<span class="code part main">\n 76 77 78 79 80\n</span>\n<br/>\nHere is your list of connections and capacities:',
                        input_type='txt',
                        form='<label class="main" for="answer2">\n What is exact amount of energy required to destroy the dome?\n <br/>\n</label>\n<input autocomplete="off" name="answer2" placeholder="..." type="text"/>\n<button>\n Submit\n</button>',
                        solution='<label class="main">\n Your answer was\n <span class="b i">\n  50512\n </span>\n .\n</label>',
                    ),
                ]
                db.session.add_all(sub_entries)
                print("Inserted html.")

        if "solutions" in table_names:
            if not db.session.query(Solution).first():
                solutions = [
                    Solution(
                        part1="SHE WILL RISE. HER LIGHT WILL BLIND THE STARS.",
                        part2="EOS"
                    ),
                    Solution(
                        part1="EXPLORING THE COSMOS: AN INCREDIBLE JOURNEY THROUGH SPACE ONE GALAXY AT A TIME.",
                        part2="CADET YOUR NEXT MISSION IS LOCATED IN THE CARGO HOLD"
                    ),
                    Solution(
                        part1="THE GODDESS IS COMING. TIME'S ALMOST UP!",
                        part2="FUEL UP CADET.YOU'LL NEED YOUR STRENGTH."
                    ),
                    Solution(
                        part1="GREEN SALAD",
                        part2="177,136"
                    ),
                    Solution(
                        part1="7462",
                        part2="958013"
                    ),
                    Solution(
                        part1="SSCSC",
                        part2="ZIRCONIUM DIOXIDE CERAMIC HEAT SINK"
                    ),
                    Solution(
                        part1="<({%=!+`<%{>",
                        part2="ACCESS OFFICE COFFEE"
                    ),
                    Solution(
                        part1="653",
                        part2="1625"
                    ),
                    Solution(
                        part1="289",
                        part2="424"
                    ),
                    Solution(
                        part1="418",
                        part2="50512"
                    ),
                ]
                db.session.add_all(solutions)
                print("Inserted solutions.")

        db.session.commit()


if __name__ == '__main__':
    main()
