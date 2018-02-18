#! python3
# Inspired by https://youtu.be/ufaOgM9QYk0

import urllib.request
import re
import random
import os
from pprint import pprint
import time
import copy
import sys
import traceback
import queue
import datetime
import threading

# pip
import telepot
import telepot.namedtuple
from telepot.loop import OrderedWebhook
import pytz
import emoji


# custom
from . import mytoken
from . import mensa
from . import users



class Speak:
    def __init__(self, language="Deutsch"):
        self.languages = ["Deutsch", "English"]
    
        self.defaultLanguage = self.languages.index(language)

        self.i = self.defaultLanguage
        
        self.missing = [{}, {}]
        
        self._english = {
            '%s: %s': '%s: %s',
            ':fork_and_knife_with_plate: *%s*': ':fork_and_knife_with_plate: *%s*',
            '@OpenMensaRobot _%d_': '@OpenMensaRobot _%d_',
            '[%s](https://openmensa.org/c/%d/%s)': '[%s](https://openmensa.org/c/%d/%s)',

            'Verstanden!': 'Got it!',
            'Erledigt!': 'Done!',
            'Ok!': 'Ok!',
            'gespeichert': 'saved',
            'entfernt': 'removed',
            'Nein': 'No',
            'Ja': 'Yes',
            'das verstehe ich nicht' : 'I don\'t understand',
            'Wissenschaftler haben herausgefunden, dass es sich um ein %s handelt.\n' : 'Exports say it\'s a %s.\n',
            'was soll ich damit?!' : 'I don\'t know what to do with that.',

            'Tastatur': 'Keyboard',

            'Tut mir leid. %s': 'I\'m sorry. %s',
            'Sorry. %s': 'Sorry. %s',

            '%d Stunden': '%d hours',
            '%d Minuten': '%d minutes',
            '%d Sekunden': '%d seconds',
            '1 Stunde': '1 hour',
            '1 Minute': '1 minute',
            '1 Sekunde': '1 second',
            ' und ': ' and ',

            'Heute': 'Today',
            'Morgen': 'Tomorrow',

            'Montag': 'Monday',
            'montag': 'monday',
            'Dienstag': 'Tuesday',
            'dienstag': 'tueday',
            'Mittwoch': 'Wednesday',
            'mittwoch': 'wednesday',
            'Donnerstag': 'Thursday',
            'donnerstag': 'thursday',
            'Freitag': 'friday',
            'freitag': 'friday',
            'Samstag': 'Saturday',
            'samstag': 'saturday',
            'Sonntag': 'Sunday',
            'sonntag': 'sunday',

            'Geschlossen' : 'Closed',
            '%s: Geschlossen' : '%s: Closed',
            'Geschlossen. :crying_face: Die Mensa %s ist am %s geschlossen. Keine Speisepläne gefunden.\nSiehe auch [openmensa.org/c/%d](https://openmensa.org/c/%d/)': 'Closed. :crying_face: The canteen %s is closed on %s. No menus were found.\nMore at [openmensa.org/c/%d](https://openmensa.org/c/%d/)',
            'Geschlossen. :loudly_crying_face: Die Mensa %s ist in nächster Zeit geschlossen. Keine Speisepläne gefunden.\nSiehe auch [openmensa.org/c/%d](https://openmensa.org/c/%d/)': 'Closed. :loudly_crying_face: The canteen %s is closed. No menus were found.\nMore at [openmensa.org/c/%d](https://openmensa.org/c/%d/)',
            'Kein Speiseplan gefunden' : 'No menu found',
            'Kein Speiseplan für %s gefunden.' : 'No menu for %s found',
            'ich konnte die Mensa nicht finden' : 'I could not find that canteen',
            'die Mensa %d kann ich nicht finden' : 'I could not find the canteen %d',
            'nichts gefunden.': 'nothing found.',
            'Daten veraltet!' : 'Information is outdated!',
            'Klick unten auf den :anticlockwise_arrows_button: um den aktuellen Plan zu erhalten' : 'Please click on the :anticlockwise_arrows_button: button under the message to get the latest menu',
            'zu viele Suchergebnisse!\nDu kannst es mit einem spezifischeren Suchbegriff versuchen' : 'too many search results!\nCould you try a more specific search query',
            'Zu viele Ergebnisse': 'Too many search results',
            'zu viele Ergebnisse. Bitte spezifiere den Suchbegriff': 'Too many results, please be more specific',
            'Oder gib einen spezifischen Suchbegriff ein, damit du nur ein Ergebnis erhältst, dann wird der Speiseplan direkt angezeigt': 'Or be more specific next time. If you receive only one search result, I can directly send you the canteen menu',
            '\n\nBeispiel:\n@OpenMensaRobot %s\n\nOder gibt die ID der Mensa an:\n@OpenMensaRobot %d': '\n\nExample:\n@OpenMensaRobot %s\n\nOr use the unique mensa id:\n@OpenMensaRobot %d',

            'Pushbenachrichtigungen aktiviert. Du erhälst um %s Uhr ': 'Notifications activated. You\'ll receive a message at %s ',
            'Pushbenachrichtigungen aktiviert. Du erhälst um %d:%02d Uhr ': 'Notifications activated. You\'ll receive a message at %d:%02d ',
            'Pushbenachrichtigungen deaktiviert :neutral_face:': 'Notifications disabled :neutral_face:',
            'automatisch den Speiseplan deiner Favoriten geschickt.\n': 'with the menu of your favorite canteens.\n',
            '/push _hh:mm_ um die Uhrzeit für die Benachrichtigungen festzulegen.\n': '/push _hh:mm_ to set the time for notifications.\n',
            '/push Pushbenachrichtigungen aktivieren. Du erhälst automatische den heutigen Speiseplan deiner Favoriten geschickt.\n': '/push Enable notifications. You\'ll automatically receive the daily menu of your favorite canteens.\n',
            '/disablepush um die Pushbenachrichtigungen wieder auszuschalten.\n': '/disablepush to deactivate notifications.\n',
            '/disablePush Pushbenachrichtigungen wieder ausschalten.\n': '/disablePush Deactivate notifications.\n',
            '/pushLoudly um den Benachrichtigungston für die Speisepläne einzuschalten.\n': '/pushLoudly to activate the sound/bell for notifications.\n',
            '/pushLoudly Benachrichtigungston für die Speisepläne einschalten.\n': '/pushLoudly Enable sound/bell for notifications.\n',
            '/pushSilently um den Benachrichtigungston für die Speisepläne auszuschalten.\n': '/pushSilently to disable the sound/bell for notifications.\n',
            '/pushSilently Benachrichtigungston für die Speisepläne ausschalten.\n': '/pushSilently Disable the sound/bell for notifications.\n',
            ':bell: Benachrichtigungston für Pushbenachrichtigungen aktiviert': ':bell: Sound for notifications enabled',
            ':bell_with_slash: Benachrichtigungston für Pushbenachrichtigungen deaktiviert :zipper-mouth_face:': ':bell_with_slash: Sound for notifications disabled :zipper-mouth_face:',
            'Der Benachrichtigungston ist ausgeschaltet.\n': 'Notification sounds are disabled.\n',
            'Der Benachrichtigungston ist eingeschaltet.\n': 'Notification sounds are activated\n',

            'Nächste Nachricht in ungefähr %s.': 'Next notification in approximately %s.',

            '/enableEmojis Emojis in Speiseplänen anzeigen\n': '/enableEmojis to enable emojis in canteen menus\n',
            '/disableEmojis Keine Emojis in Speiseplänen anzeigen\n': '/disableEmojis to disable emojis in canteen menus\n',
            'Emojis in Speiseplänen deaktiviert :fearful_face:': 'Emojis in menus are now deactivated :fearful_face:',
            ':thumbs_up: Emojis in Speiseplänen aktiviert :smiling_cat_face_with_heart-eyes:': ':thumbs_up: Emojis in menus are now activated :smiling_cat_face_with_heart-eyes:',

            'Sende mir einfach deine aktuelle Position oder schreibe mir den Namen deiner Stadt\n': 'Simply send your current GPS location or write me the name of your city or canteen\n',

            'Position senden': 'Send GPS position',
            'in deiner Nähe (%dkm) habe ich nichts gefunden.': 'I did not find any canteens in your area (%dkm)',
            'Klick auf deine Mensa:': 'Click on your canteen:',

            '/map{id} Wegbeschreibung\n': '/map{id} Show map or address of canteen\n',
            'für %s habe ich keine genaue Position oder Adresse' : 'unfortunately, I don\'t have a position or adress for %s',

            'Andere Befehle:\n': 'Other commands:\n',
            'Folgende Befehle könnten nützlich sein:': 'The following commands could now be useful:',

            '/merke{id} Mensa als Favorit speichern\n': '/merke{id} Save canteen in favorites\n',
            '/favoriten um deine aktuellen Favoriten anzusehen.\n': '/favoriten to view your favorite canteens.\n',
            'Du hast noch keine Favoriten.\n': 'You do not have any favorites yet.\n',
            'setze Favoriten mit /merke _id_\noder mit dem :red_heart: unter dem Speiseplan': 'add a canteen to your favorites with /merke _id_\nor with the :red_heart: under the canteen menu',
            'Deine Favoriten:\n%s\n\nUm eine Mensa zu entfernen, klick auf den Mensa Link und dann auf das :broken_heart:': 'Your favorites:\n%s\n\nTo remove a canteen, click on the canteen link and then on the :broken_heart:',


            '/off Benachrichtigungen ausschalten und alle auf dem Server gespeicherten Daten löschen\n': '/off Turn off notifications and remove all personal data from my server\n',
            '/finde {name} Finde Mensen\n': '/find {name} Find canteens by name\n',
            '/mensa{id} oder /heute{id}: Speiseplan anzeigen\n': '/mensa{id} or /heute{id}: Show canteen menu\n',
            '/vergiss{id} Favorit entfernen\n': '/vergiss{id} Remove from favorites\n',

            '*Account gelöscht* :confused_face:\n\nAlle persönlichen Daten auf meinem Server wurden entfernt.': '*Account deleted* :confused_face:\n\nAll your personal has been removed from my server.',


            '/morgen{id} Speiseplan für folgenden Tag anzeigen\n': '/morgen{id} Show tomorrow\'s menu\n',
            '/favoriten Zeige alle mit /merke gespeicherten Mensen\n': '/favoriten Show the canteens that you saved with /merke\n',
            'Das ist ein Bot für Informationen von [openmensa.org](https://openmensa.org/)\n\nBrauchst du Hilfe?': 'This is a bot for [openmensa.org](https://openmensa.org/)\n\nNeed help?',



            '/feedback Hinterlass dem Entwicklerteam eine Nachricht.' : '/feedback Leave a note to the developers.',
            'Dein bisheriges Feedback:': 'Your current feedback:',
            'Sende mir einfach eine Nachricht mit dem Tag #feedback zum Beispiel so:' : 'Just send me a message with the hashtag #feedback like this:',
            'Euer Bot ist ganz doof #feedback' : 'Your bot sucks #feedback',
            'Die Nachricht wird dann gespeichert und das Entwicklerteam schaut sie sich irgendwann an, vielleicht kontaktieren wir dich auch.' : 'The message will be saved and my developers will probably read it someday.',
            'Du kannst jederzeit alle deine persönlichen Daten inklusiv deines Feedbacks mit /off vom Server löschen.' : 'Remember you can remove all your personal information including your feedback from my server with the command /off.',
        
        }
        
        self._dateFormat = ["%weekday, den %d.%m.", "%A, %B %e"]
        
        
        self.data = [None, self._english]
        
    def getDefaultLanguage(self):
        return self.languages[self.defaultLanguage]
        
    def setLanguage(self, name):
        if name in self.languages:
            self.i = self.languages.index(name)
        else:
            self.i = self.defaultLanguage
            print("Language does not exist: %s" % name)
            
            
    def dateFormat(self):
        return self._dateFormat[self.i]
        
    def s(self, str):
        if self.i > 0:
            if str in self.data[self.i]:
                return self.data[self.i][str]
            else:
                self.missing[self.i][str] = None
                try:
                    print("Translation in %s needed for: \"%s\"" % (self.languages[self.i], str.encode().decode("ascii", errors='ignore')))
                except:
                    print("Translation in %s needed")
                    
        return str

    def __addDot(self, s):
        if re.search("\w$", s):
            return "%s." % s
        else:
            return s


    def hello(self, text=""):
        greets = [ 'Shalom שלום', "Hey!", "¡Hola!", "God dag.", "Hallo!", "Guten Tag!", "Peace :victory_hand:"]

        s = random.choice(greets)
        if len(text) > 0:
            s += " " + text

        return s


    def error(self, text=""):
        msg = [self.s(":face_screaming_in_fear: Ein fEhLer"),
               self.s("So war das nicht geplant. :disappointed_face:\n"),
               self.s(":warning: Upps. Da ist ein Fehler aufgetaucht.\n")]

        s = random.choice(msg)

        if len(text) > 0:
            s += " " + text[0].upper() + text[1:]

        return self.__addDot(s)

    def advice(self, text=""):
        msg = [":index_pointing_up:",
               ":owl:",
               ":light_bulb:"]

        s = random.choice(msg)

        if len(text) > 0:
            s += " " + text[0].upper() + text[1:]

        return self.__addDot(s)



    def wait(self):
        msg = [self.s(":snail: Eine Sekunde."),
               self.s(":hourglass_with_flowing_sand: Eine alte Fraue ist kein D-Zug."),
               self.s("It'll be here at any moment :turtle:"),
               self.s("Ich arbeite, also bin ich. :hourglass_with_flowing_sand:"),
               self.s(":OK_button::COOL_button: aber es dauert einen Moment")]

        return random.choice(msg)


    def success(self, text=""):
        yes = [ self.s("Verstanden!"), self.s("Erledigt!"), self.s("Ok!")]

        s = random.choice(yes)

        if len(text) > 0:
            s += " " + text[0].upper() + text[1:]

        return self.__addDot(s)


    def apologize(self, text):
        apologies = [self.s("Tut mir leid. %s"), self.s("Sorry. %s")]
        text = text[0].upper() + text[1:]
        return self.__addDot(random.choice(apologies) % text)


    def randomQuote(self):
        msg = ["Når katten er borte, danser musene på bordet.",
               "Som faren går fyre, kjem sonen etter.",
               "Bedre føre var enn etter snar.",
               "Far, får får får? Nei, får får ikke får, får får lam.",
               "Look at you, you look so superficial.",
               "Lieber in der dunkelsten Kneipe als am hellsten Arbeitsplatz."]

        return random.choice(msg)



class Bot:

    def __init__(self, mensaCacheFile, userFile):
        self.__startTime = time.time()
        
        self.__stopFlag = [False]

        self.status = "Loaded"
        self.send = {}
        self.speak = Speak()
        self.s = self.speak
        self.informStatusTo = 123456789 # TODO set to admin id

        self.openmensa = mensa.OpenMensa(cacheFile=mensaCacheFile)

        self.users = users.Users(userFile=userFile, nowTime=self.timeNow().time())

        emoji_list = {
                   ":fish:" : ["(?<!lachs)forelle","lachs","karpfen","hecht", "barsch", "makrele", "kabeljau", "(\b|\s|^)aal",
                               "dorsch", "pangasius", "(\b|\s|^)tuna", "hering", "saibling", "zander", "wels", 
                               "flunder", "barbe", "butt(?!er)", "scholle","seezunge", "tilapia", "scharbe", "dorade",
                               "eisflunder", "lotte[^n]", "seeteufel",  "steinbeißer", "skantjes", "(\b|\s|^)hoki",
                               "(?<!tinten)fisch"],
                   ":squid:" : ["tintenfisch", "calamari", "calamares", "kalmar", "chipirones"],
                   ":shark:" : ["chillerlocke", "seeaal"],
                   ":octopus:" : ["oktopus", "pulpo","kraken"],
                   ":fried_shrimp:" : ["shrimp","garnelen","krebs","krabbe"],
                   ":cow:" : ["[^t]rind", "kalb", "strogano\w{1,2}", "tafelspitz", "entrec\wte", "rumpsteak", "ossobuco"],
                   ":pig:" : ["(?<!wild)schwein","pork", "minutensteak", "(\b|\s|^)krustenbraten", "kasse?ler", "currywurst", "bratwurst"],
                   ":horse:" : ["pferd"],
                   ":boar:" : ["wildschwein"],
                   ":goat:" : ["ziegen"],
                   ":deer:" : ["hirsch","(\b|\s|^)reh"],
                   ":rabbit:" : ["hasen"],
                   ":sheep:" : ["lamm","lämmer","hammel", "schaf[^ft]"],
                   ":rooster:" : ["huhn","geflügel","hähnchen","hühn", "hendl", "broiler"],
                   ":turkey:" : ["truthahn","pute","[^\:]turkey"],
                   ":duck:" : ["(\b|\s|^)ente"],
                   ":panda_face:" : ["bambus"],
                   ":mushroom:" : ["pilz","schwammerl","champignon","pfifferling","morcheln","kräuterseitling"],
                   ":tangerine:" : ["orange","mandarine","apfelsine"],
                   ":lemon:" : ["[^\:]lemon", "zitrone", "limone"],
                   ":peach:" : ["pfirsich", "nektarine", "aprikose","shiitake"],
                   ":baguette_bread:" : ["baguette(\b|\s|$)"],
                   ":grapes:" : ["\btrauben"],
                   ":tomato:" : ["tomate","pomodor"],
                   ":strawberry:" : ["erdbeer"],
                   ":banana:" : ["banane"],
                   ":cherries:" : ["kirsch(?!(\s|-)?tomaten)"],
                   ":wine_glass:" : ["(?<!(eiß|sch))wein"],
                   ":eggplant:" : ["aubergine"],
                   ":ear_of_corn:" : ["mais","polenta"],
                   ":carrot:" : ["karotte","möhre","gelbe rübe"],
                   ":cucumber:" : ["gurke"],
                   ":peanuts:" : ["erdn[uü]ss"],
                   ":potato:" : ["(?<!süß)kartoffel", "[^\:]potato[^\:]", "patatas"],
                   ":roasted_sweet_potato:" : ["süßkartoffel"],
                   ":honey_pot:" : ["honig"],
                   ":poultry_leg:" : ["schlegel"],
                   ":cheese_wedge:" : ["[^\:]cheese", "(?<!fleisch)käse", "gouda", "gorgonzola", "mozzarella", "formaggi", "parmesan", 
                                       "grana padano", "ricotta", "cordon bleu"],
                   ":pizza:" : ["[^\:]pizza", "lahmacun"],
                   ":hamburger:" : ["[^\:]burger"],
                   ":burrito:" : ["burrito","wrap","fajita"],
                   ":french_fries:" : ["pommes frites", "pommes(?!(\s|-)frites)", "twisters"],
                   ":stuffed_flatbread:" : ["döner"],
                   ":green_salad:" : ["salat"],
                   ":bacon:" : ["[^\:]bacon","speck"],
                   ":spaghetti:" : ["spaghetti","pasta","penne","tagliatelle","spirelli","farfalle","makkaroni", 
                                    "maccheroni", "bucatini"],
                   ":cooked_rice:" : ["risotto", "gemüsereis", "kräuterreis", "jasminreis", "sushireis", 
                                      "wildreis", "mochireis", "kurkumareis", "butterreis", "basmatireis", 
                                      "kornreis", "naturreis", "milchreis", "duftreis", "risi(-|\s)?(p|b)isi",
                                      "ingwer", "pfannenreis", "djuvecreis", "(\b|\s|^|-)reis", "pila[fw]"],
                   ":bento_box:" : ["sushi","bento"],
                   ":shortcake:" : ["(\b|\s|^)kuchen","torte(?!(llini|lloni))"],
                   ":cookie:" : ["keks","cookie"],
                   ":pancakes:" : ["cr.pe", "eierkuchen", "palatschinken", "pfannkuchen", "rührei", "omelett", "(\w|\s|^)pancake(\s|$|\w)"],
                   ":chocolate_bar:" : ["schokolade", "[^\:]chocolat"],
                   ":ice_cream:" : ["(\b|\s|^)eis(\b|\s|$)"],
                   ":doughnut:" : ["(\b|\s|^)doughnut", "donut"],
                   ":hot_beverage:" : ["kaffee"],
                   ":beer_mug:" : ["bier(\b|\s)"],
                   ":wrapped_gift:" : ["überraschung"],
                   ":avocado:" : ["avocado","guacamole"],
                   ":kiwi_fruit:" : ["(\s|^|\w)kiwi"],
                   ":pineapple:" : ["ananas"],
                   ":red_apple:" : ["apfel","äpfel"],
                   ":pear:" : ["birne"],
                   ":glass_of_milk:" : ["(\b|\s|^)milch(\b|\s|$)"],
                   ":victory_hand:" : ["vegan"],
                   ":green_heart:" : ["vegetarisch"],
                   ":custard:" : ["flan", "karamell?(\s|-)?pudding", "cr.me br.l.{1,2}", "cr\wme (c|k)aramell?", "crema catalana","crema cremada","brönnti"],
                   ":hot_pepper:" : ["chili","paprika","pepp?eroni"],
                   ":fire:" : ["feurig"],
                   ":smiling_face_with_horns:" : ["dia[bv]olo", "teufel","teufli"],
                   ":shallow_pan_of_food:" : ["pfanne"],
                   ":steaming_bowl:" : ["suppe", "\bramen"],
                   ":dragon:" : ["asia"],
                   ":face_with_medical_mask:" : ["knoblauch", "aioli"],
                   
                   ":<gr>:" : ["griechisch","gyros","tzatziki","bifteki","so?u(f|v)laki", "rhodos"],
                   ":<id>:" : ["indonesisch","goreng","satay","saté","(\s|^|\w)sate"],
                   ":<rs>:" : ["serbisch" ,"\wevap\wi\wi"],
                   ":<hu>:" : ["ungarisch", "szeged", "esterh\wzy"],
                   ":<gb>:" : ["englisch"],
                   ":<in>:" : ["indisch", "aloo(\s|-)?gobi", "samosa", "raita", "kanpur", "punjabi", "tandoori","tikka(\s|-)?masala"],
                   ":<th>:" : ["thai","khao","keng","tom(\s|-)?yam"],
                   ":<fr>:" : ["französisch", "proven\wi?al", "els[aä]ss"],
                   ":<us>:" : ["amerikanisch","georgia","st. louis"],
                   ":<cn>:" : ["chinesisch", "kanton", "china(?!(\s|-)?kohl)", "wan(\s|-)?tan", "chop(\s|-)?suey","kung(\s|-)?pa?o", "szechuan", "peking", "shanghai", "hong kong", "feng(\s|-)?shui"],
                   ":<jp>:" : ["japanisch", "sushi", "teriyaki"],
                   ":<tr>:" : ["türkisch", "döner","yufka","lahmacun","börek"],
                   ":<it>:" : ["italienisch", "calabria", "toskan", "florentiner", "lasagne", "gnocchi", "bolognese", "ravioli", "tortelloni","tortellini","cannelloni", "linguin"],
                   ":<es>:" : ["spanisch", "bravas", "arrugadas", "paella", "arroz", "gazpacho", "empanada"],
                   ":<pl>:" : ["polnisch"],
                   ":<mx>:" : ["mexi(c|k)"],
                   ":<ar>:" : ["argentin"],
                   ":<br>:" : ["brasili"],
                   ":<ck>:" : ["chile"],
                   ":<pe>:" : ["peru"],
                   ":<nl>:" : ["holländisch", "niederländisch","flämisch"],
                   ":<se>:" : ["swedisch", "köttbullar"],
                   ":<eg>:" : ["ägyptisch"],
                   ":<tn>:" : ["tunesisch", "minztee"],
                   ":<dz>:" : ["algerisch"],
                   ":<ma>:" : ["marokkanisch"],
                   ":<az>:" : ["aserbaidschan"],
                   ":<by>:" : ["weißrussisch"],
                   ":<ru>:" : ["(?<!weiß)russisch"],
                   ":<bg>:" : ["bulgarisch"],
                   ":<ba>:" : ["bosnisch"],
                   ":<cz>:" : ["tschechisch"],
                   ":<dk>:" : ["dänisch"],
                   ":<ir>:" : ["iranisch", "persisch"],
                   ":<fi>:" : ["finnisch"],
                   ":<fo>:" : ["färöisch"],
                   ":<ch>:" : ["schweiz", "tessin"],
                   ":<at>:" : ["österreich", "tirol", "kärnten", "steiermark"],
                   ":<il>:" : ["hebräisch", "koscher"],
                   ":<hr>:" : ["kroatisch", "croatia"],
                   ":<am>:" : ["armenisch"],
                   ":<is>:" : ["isländisch"],
                   ":<ge>:" : ["georgisch"],
                   ":<ca>:" : ["kanadisch", "ahorn"],
                   ":<lu>:" : ["luxemburg"],
                   ":<mn>:" : ["mongolisch"],
                   ":<no>:" : ["norwegisch"],
                   ":<pt>:" : ["portugiesisch"],
                   ":<ro>:" : ["rumänisch"],
                   ":<sk>:" : ["slowakisch"],
                   ":<si>:" : ["slowenisch"],
                   ":<so>:" : ["somali"],
                   ":<al>:" : ["albanisch"],
                   ":<sy>:" : ["syrisch"],
                   ":<ua>:" : ["ukrainisch", "borschtsch"],
                   ":<vn>:" : ["vietnam"],
                   ":<ph>:" : ["philippin"],
                   ":<kr>:" : ["korea", "kimchi", "jjigae"]
                   }
        
        self.emoji_re = {}
        for emo in emoji_list:
            self.emoji_re[emo] = []
            for q in emoji_list[emo]:
                self.emoji_re[emo].append(re.compile(q,flags=re.MULTILINE|re.IGNORECASE))

                
        self.setLanguage(self.speak.getDefaultLanguage())

        
    def setLanguage(self, lang):
        self.speak.setLanguage(lang)

        self.weekdays = [self.s.s("Montag"),self.s.s("Dienstag"),self.s.s("Mittwoch"),self.s.s("Donnerstag"),self.s.s("Freitag"),self.s.s("Samstag"),self.s.s("Sonntag")]
        self.weekdays_lower = [self.s.s("montag"),self.s.s("dienstag"),self.s.s("mittwoch"),self.s.s("donnerstag"),self.s.s("freitag"),self.s.s("samstag"),self.s.s("sonntag")]
        self.todayWord = self.s.s("Heute")
        self.tomorrowWord = self.s.s("Morgen")
                
    def timeNow(self):
        berlin = pytz.timezone('Europe/Berlin')
        return datetime.datetime.now(berlin)


    def sendRawMessage(self, cid, text, parse_mode=None, disable_notification=None, reply_markup=None):
        ret = self.bot.sendMessage(cid, text, parse_mode=parse_mode, disable_notification=disable_notification, reply_markup=reply_markup)
        if not cid in self.send:
            self.send[cid] = []
        self.send[cid].append(("m", text, ret))

        return ret


    def sendMessage(self, cid, text, parse_mode=None, disable_notification=None, reply_markup=None):
        text = text[0].upper() + text[1:]
        
        text = emoji.emojize(text)
        
        N = 1600
        
        # Split long message up
        # otherwise telegram will automatically remove emojis from long messages. 
        while len(text) > N:
            # Try to split at newline
            m = re.compile(r"\n|$", flags=re.MULTILINE).search(text, pos=N-50)
            if not m: # try to split at whitespace
                m = re.compile("\s+", flags=re.MULTILINE).search(text, pos=N-50)
                if not m: # try to split at wordend
                    m = re.compile("\b\s*", flags=re.MULTILINE).search(text, pos=N-50)
                
                
            if not m:
                # split anywhere
                text, rest = text[0:N-3] + "...", text[N-5:].strip()
            else:
                text, rest = text[0:m.start()], text[m.end():].strip()
            
            if len(rest) == 0:
                text = rest
                break
            else:
                self.sendRawMessage(cid, text, parse_mode=parse_mode, disable_notification=disable_notification)
            
            text = rest
        
        return self.sendRawMessage(cid, text, parse_mode=parse_mode, disable_notification=disable_notification, reply_markup=reply_markup)


    def deleteMessage(self, cid, msg=None):
        # deleteMessage(123, 758455)
        # deleteMessage(123, msg_obj)
        # deleteMessage(msg_obj)
        if msg is None:
            cid, mid = cid["chat"]["id"], cid["message_id"]
        elif isinstance(cid, int) and isinstance(msg, int):
            mid = msg
        elif isinstance(cid, int):
            mid = msg["message_id"]
        else:
            raise Exception("Wrong arguments")

        self.bot.deleteMessage((cid, mid))


    def sendMensasNear(self, cid, lat, lng):
        dist = 7
        mensas = self.openmensa.findMensaNear(lat=lat, lng=lng, dist=dist)
        if len(mensas) == 0:
            dist = 15
            mensas = self.openmensa.findMensaNear(lat=lat, lng=lng, dist=dist)
            if len(mensas) == 0:
                dist = 25
                mensas = self.openmensa.findMensaNear(lat=lat, lng=lng, dist=dist)
                if len(mensas) == 0:
                    return self.sendMessage(cid, self.speak.apologize(self.s.s("in deiner Nähe (%dkm) habe ich nichts gefunden.") % dist))

            
            
        googlemaps = 'https://maps.googleapis.com/maps/api/staticmap?size=700x1200&maptype=roadmap&markers='+urllib.parse.quote_plus('color:0x00DDBB|%f,%f' % (lat,lng))
        s = [self.s.s("Klick auf deine Mensa:")]
        i = 0
        labels = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 30
        for mensa in mensas:
            try:
                d = self.openmensa.distance(lat, lng, mensa["coordinates"][0], mensa["coordinates"][1])
                t = "%s: /mensa%d %s (%.1fkm)" % (labels[i], mensa["id"], mensa["name"], d)
            except:
                t = "%s: /mensa%d %s" % (labels[i], mensa["id"], mensa["name"])
                
            s.append(t)
            
            googlemaps += "&markers="+ urllib.parse.quote_plus("color:0x%02x0000|label:%s|%f,%f" % (255 - i, labels[i], mensa["coordinates"][0], mensa["coordinates"][1]))

            i += 1
        
        
        s.append(self.s.s("Mehr unter [openmensa.org](https://openmensa.org/#14/%.4f/%.4f)") % (lat, lng))
        s = "\n\n".join(s)
        
        
        googlemaps += "&key=abc123456789_abcdefgh123" # TODO add your google maps API key here
        
        self.bot.sendPhoto(cid, googlemaps)
        
        self.sendMessage(cid, s, parse_mode="Markdown")
        

    def __formatDate(self, datetime_obj, format):
        today = self.timeNow().date()
        tomorrow = today + datetime.timedelta(days=1)
        if self.todayWord is not None and datetime_obj.date() == today:
            return self.todayWord
        elif self.tomorrowWord is not None and datetime_obj.date() == tomorrow:
            if "%weekday" in format:
                format = format.replace("%weekday", self.tomorrowWord)
                return datetime_obj.strftime(format)
            else:
                return self.tomorrowWord
        else:
            if "%weekday" in format:
                if self.weekdays is not None:
                    w = self.weekdays[datetime_obj.weekday()]
                else:
                    w = "%A"
                format = format.replace("%weekday", w)
            if not "%y" in format.lower() and datetime_obj.date().year != today.year: # Add year in case it's different
                format += " %Y"
            
            return datetime_obj.strftime(format)
            
    def __escapeMarkdown(self, str):
        return str.replace("*","\\*").replace("_","\\_").replace("`","\\`")

    def formatMensaMeals(self, daymealsret, canteenid=None, mensa=None):
        day, meals, ret = daymealsret
        if canteenid is None:
            canteenid = mensa["id"]

        date = None
        if day is not None:
            datetime_day = datetime.datetime.strptime(day, '%Y-%m-%d')
            date = self.__formatDate(datetime_day, format=self.s.dateFormat())

        if ret == False:
            if mensa is not None and "city" in mensa:
                preview = self.s.s("%s: Geschlossen") % mensa["city"]
                if date is not None:
                    s = self.s.s("Geschlossen. :crying_face: Die Mensa %s ist am %s geschlossen. Keine Speisepläne gefunden.\nSiehe auch [openmensa.org/c/%d](https://openmensa.org/c/%d/)") % (mensa["name"],date,canteenid,canteenid)
                else:
                    s = self.s.s("Geschlossen. :loudly_crying_face: Die Mensa %s ist in nächster Zeit geschlossen. Keine Speisepläne gefunden.\nSiehe auch [openmensa.org/c/%d](https://openmensa.org/c/%d/)") % (mensa["name"],canteenid,canteenid)
            else:
                preview = self.s.s("Geschlossen")
                if date is not None:
                    s = self.s.s("Geschlossen. :crying_face: Die Mensa ist in am %s geschlossen. Keine Speisepläne gefunden.\nSiehe auch [openmensa.org/c/%d](https://openmensa.org/c/%d/)") % (date,canteenid,canteenid)
                else:
                    s = self.s.s("Geschlossen. :loudly_crying_face: Die Mensa ist in nächster Zeit geschlossen. Keine Speisepläne gefunden.\nSiehe auch [openmensa.org/c/%d](https://openmensa.org/c/%d/)") % (canteenid,canteenid)
            return (preview, s)



        if mensa is not None and "city" in mensa:
            preview = self.s.s("%s: %s") % (mensa["city"], date)
        else:
            preview = date
        s = []

        if mensa is not None:
            s.append(self.s.s(":fork_and_knife_with_plate: *%s*") % self.__escapeMarkdown(mensa["name"]))
        else:
            s.append(self.s.s("@OpenMensaRobot _%d_") % canteenid)

        s.append(self.s.s("[%s](https://openmensa.org/c/%d/%s)") % (date, canteenid, day))

        if len(meals) == 0:
            preview += " " + self.s.s("Kein Speiseplan gefunden")
            s.extend(["", self.s.s("Kein Speiseplan für %s gefunden.") % date])
        else:
            preview += meals[0]["name"][0:50]
            last_cat = ""
            for meal in meals:
                t = ""
                if meal["category"] != last_cat:
                    last_cat = meal["category"]
                    t += "\n*%s*:\n" % self.__escapeMarkdown(meal["category"].strip())
                t += self.__escapeMarkdown(meal["name"].strip())
                s.append(t)

        return (preview, "\n".join(s))


    def getMensaMealsFormatted(self, canteenid, offsetDays=0, at_day=None, uid=None):
        mensa = self.openmensa.getMensa(canteenid)
        if mensa is None:
            return None, None
        daymealsret = self.openmensa.getNextMeal(canteenid, offsetDays=offsetDays, at_day=at_day)
        

        preview, text = self.formatMensaMeals(daymealsret=daymealsret, canteenid=canteenid, mensa=mensa)
        
        if uid is None or self.users.showEmojis(uid):
            text = self._decorateWithEmojis(text)
        
        return preview, text
        
        
    def getSendMensaMealsMessage(self, cid, canteenid, uid=None, offsetDays=0, at_day=None):
        if uid is None:
            uid = cid

        preview, text = self.getMensaMealsFormatted(canteenid, offsetDays=offsetDays, at_day=at_day, uid=uid)

        if preview is None:
            return {
                "cid" : cid,
                "text" : self.speak.apologize(self.s.s("ich konnte die Mensa nicht finden")),
                "reply_markup" : None,
                "parse_mode" : "Markdown"
                }
        
        if offsetDays == 0:
            nextButton = (":right_arrow:", "/mensaNext%d" % canteenid)
            reloadButton = (":anticlockwise_arrows_button:", "/mensa%d" % canteenid)
        else:
            nextButton = (":right_arrow:", "/mensaNext%d_%d" % (canteenid, offsetDays + 1))
            reloadButton = (":anticlockwise_arrows_button:", "/mensaNext%d_%d" % (canteenid, offsetDays))

        if self.users.isFavorite(uid, canteenid):
            favoriteButton = (":broken_heart:", "/vergiss%d" % canteenid)
        else:
            favoriteButton = (":red_heart:", "/merke%d" % canteenid)
        
        return {
            "cid" : cid,
            "text" : text, 
            "reply_markup" : self._inlineKeyBoard(favoriteButton, reloadButton, (":world_map:", "/map%d" % canteenid), nextButton ),
            "parse_mode" : "Markdown"
            }
        
    def sendMensaMeals(self, cid, canteenid, uid=None, offsetDays=0, at_day=None, disableNotification=False):
        ret = self.getSendMensaMealsMessage(cid, canteenid, uid=uid, offsetDays=offsetDays, at_day=at_day)
        
        self.sendMessage(
            cid,
            ret["text"],
            parse_mode=ret["parse_mode"],
            reply_markup=ret["reply_markup"],
            disable_notification=disableNotification
            )


    def sendMensaFind(self, cid, query, max=50):
        mensas = self.openmensa.findMensaByString(query)
        if len(mensas) == 0:
            return self.sendMessage(cid, self.speak.apologize(self.s.s("nichts gefunden.")) + "\n" + self._decorateWithEmojis(query))

        if len(mensas) > 50:
            return self.sendMessage(cid, self.speak.apologize(self.s.s("zu viele Suchergebnisse!\nDu kannst es mit einem spezifischeren Suchbegriff versuchen")))


        s = [self.s.s("Klick auf deine Mensa:")]
        for mensa in mensas:
            t = "/mensa%d %s" % (mensa["id"], mensa["name"])
            s.append(t)

        s = "\n\n".join(s)
        self.sendMessage(cid, s, parse_mode="Markdown")


    def _keyBoard(self, buttons=None):
        Button = telepot.namedtuple.KeyboardButton

        standard = [Button(text=self.s.s("Position senden"), request_location=True)]

        if buttons:
            standard.extend(buttons)
            buttons = standard
        else:
            buttons = standard

        keyboard = telepot.namedtuple.ReplyKeyboardMarkup(
            keyboard=[
                buttons
                ],
            resize_keyboard=True)

        return keyboard



    def sendMessageWithKeyboard(self, cid, text, parse_mode=None, disable_notification=None):
        self.sendMessage(cid,
                         text,
                         reply_markup=self._keyBoard(),
                         disable_notification=disable_notification,
                         parse_mode=parse_mode
                         )

    def sendKeyboard(self, cid):
        self.sendMessageWithKeyboard(cid, self.s.s("Tastatur"))



    def _inlineKeyBoard(self, *buttons):
        inlineKeyboardButtons = [telepot.namedtuple.InlineKeyboardButton(text=emoji.emojize(item[0]), callback_data=item[1]) for item in buttons]

        keyboard = telepot.namedtuple.InlineKeyboardMarkup(inline_keyboard=[inlineKeyboardButtons])

        return keyboard


    def _inlineKeyBoardYesNo(self, yes=("Ja","ja"), no=("Nein","nein"), other=None):
        if other is None:
            return self._inlineKeyBoard(yes, no)
        else:
            return self._inlineKeyBoard(yes, no, other)

    def _flags(self, text):
        OFFSET = ord('🇦') - ord('A')
        def flag(code):
            if not code:
                return u''
            points = list(map(lambda x: ord(x) + OFFSET, code.upper()))
            try:
                return chr(points[0]) + chr(points[1])
            except ValueError:
                return ('\\U%08x\\U%08x' % tuple(points)).decode('unicode-escape')
        
        def flag_repl(matchobj):
            return flag(matchobj.group(1))
                
        text = re.sub(':\<([a-zA-Z]{2})\>:', flag_repl, text)
        
        return text
        
    def _decorateWithEmojis(self, text):
        
        # TODO if same emoji occurs multiple times in one line, just put it once at the end of the line
        
        
        
        wordend = re.compile("(,|\(|\[|\s|\b|$)", flags=re.MULTILINE)

        for emo in self.emoji_re:
            for regex in self.emoji_re[emo]:
                cursor = 0
                m = regex.search(text, pos=cursor)
                while m:
                    # find next space:
                    lastchar = m.group(0)[-1]
                    if len(lastchar.strip()) == 0: # last char in pattern is white space
                        space = m.end()-1
                    else:  # find next whitespace or end of line
                        space = wordend.search(text, pos=m.end()).start()
                    
                    # put emoji in the whitespace
                    text = text[:space] + ' '+ emo + text[space:]
                    
                    cursor = space + len(emo) + 1
                        
                    m = regex.search(text, pos=cursor)
                    
        return self._flags(text)

        
    def _timeTo(self, at_time):
        dummydate = datetime.date(2000,1,1)
        diff = datetime.datetime.combine(dummydate, at_time) - datetime.datetime.combine(dummydate, self.timeNow().time())
        seconds = diff.seconds
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        
        return h, m, s
        
        
    def _formatTimeRemaining(self, h, m, s, omit_seconds=True):
        # format output of _timeTo()
        re= []
        if h == 1:
            re.append(self.s.s("1 Stunde"))
        elif h > 0 or h < 0:
            re.append(self.s.s("%d Stunden") % h)
        
        if m == 1:
            re.append(self.s.s("1 Minute"))
        elif m > 0 or m < 0:
            re.append(self.s.s("%d Minuten") % m)
        
        if not omit_seconds or (h == 0):
            if s == 1:
                re.append(self.s.s("1 Sekunde"))
            elif s > 0 or s < 0:
                re.append(self.s.s("%d Sekunden") % s)
        
        return self.s.s(" und ").join(re)
        

    def __prepareEmojiSearch(self, text, emojis):
        text = text.replace('\ufe0f',' ').strip()

        if isinstance(emojis, str):
            emojis = [emojis]

        cats = {"hearts" : [":red_heart:", ":black_heart:",":green_heart:",":blue_heart:",":purple_heart:",":yellow_heart:",":heart_suit:"],
                "stars" : [":glowing_star:",":white_medium_star:"]}


        emojilist = []
        for x in emojis:
            if x[0] == ":":
                emojilist.append(x)
            elif x in cats:
                emojilist.extend(cats[x])
            else:
                print("emojis should start with a ':' or be a valid category.")

        d = emoji.demojize(text)

        return d, emojilist

    def _isEmoji(self, text, emojis):
        d, emojilist = self.__prepareEmojiSearch(text, emojis)

        return d in emojilist

    def _hasEmoji(self, text, emojis):
        d, emojilist = self.__prepareEmojiSearch(text, emojis)

        for x in emojilist:
            if x in d:
                return True
        return False

    def _handleMessage(self, msg, query_id=None):
        content_type, chat_type, cid = telepot.glance(msg)
        message_id = msg["message_id"]

        #pprint(msg)
        #pprint(telepot.glance(msg))


        uid = None
        uname = None
        if 'chat' in msg and 'id' in msg['chat']:
            uid = msg["chat"]["id"]
            uname = None
            if "username" in msg["chat"]:
                uname = msg["chat"]["username"]
            self.users.addUser(uid, uname)
        elif 'message' in msg and 'chat' in msg['message'] and 'id' in msg['message']['chat']:
            uid = msg['message']['chat']["id"]
            uname = None
            if "username" in msg['message']['chat']:
                uname = msg['message']['chat']["username"]
            self.users.addUser(uid, uname)
        else:
            raise Exception("Could not find user id in msg")
            
            
        self.setLanguage(self.users.getLanguage(uid, self.speak.getDefaultLanguage()))
        
        
        admin = self.informStatusTo == uid

        callbackAnswered = None
        if query_id is None:
            __returnId = cid
            def say(text, parse_mode=None, disable_notification=None, reply_markup=None):
                return self.sendMessage(__returnId, text, parse_mode=parse_mode, disable_notification=disable_notification, reply_markup=reply_markup)
        else:
            __returnId = query_id
            callbackAnswered = False
            def say(text, parse_mode=None, disable_notification=None, reply_markup=None):
                global callbackAnswered
                callbackAnswered = True
                return self.bot.answerCallbackQuery(__returnId, text=text)

                
        # Don't post in channels without @mentionmybot
        if 'chat' in msg and 'type' in msg['chat'] and msg['chat']['type'] == "channel":
            if content_type == 'text':
                if "openmensa" in msg['text'].lower():
                    for r in ["@openmensarobot", "openmensarobot", "@openmensa", "openmensa"]:
                        msg['text'] = msg['text'].lower().replace(r, " ")
                else:
                    content_type = "skip_message"
            elif content_type != 'text':
                content_type = "skip_message"
        
        if content_type == "skip_message":
            pass
            
        elif content_type == 'text':
            txt_strip = msg['text'].strip()
            txt = msg['text'].lower().strip()
            
            uname_str = self.users.getUsername(uid)
            if not uname_str:
                uname_str = "<unknown>"
            else:
                uname_str = uname_str.encode('unicode-escape').decode('ascii')
            
            print("@%s: %s" % (uname_str, emoji.demojize(txt).encode('unicode-escape').decode('ascii')))

            if admin and '/users' == txt:
                all_user_ids = self.users.getUsers()
                
                
                text = []
                peoples = self.users.getStats()
                berlin = pytz.timezone('Europe/Berlin')
                nowTimestamp = self.timeNow().timestamp()
                
                
                cat = ""
                for x in peoples:
                    if x[2] != 0:
                        datetimeObj = datetime.datetime.fromtimestamp(x[2], berlin)
                        date = datetimeObj.strftime('%Y-%m-%d')
                        time = datetimeObj.strftime('%H:%M:%S')
                        
                        if not x[3] and (nowTimestamp - x[2]) / (60*60*24) > 14: # Skip older than two weeks and no feedback
                            continue
                        
                    else:
                        date = time = "<sometime>"
                    
                    if cat != date:
                        cat = date
                        text.append("\n*%s*" % date)
                        
                    feedbackLink = "\n/askForFeedback%d\n" % x[0]
                    if x[3]:
                        feedbackLink = "\n:love_letter: /readFeedback%d\n" % x[0]
                    text.append("@%s (%s) %s" % (self.__escapeMarkdown(x[1]), time, feedbackLink))
                
                self.sendMessage(cid, "\n".join(text), parse_mode="Markdown")
                
            elif admin and txt.startswith("/readfeedback"):
                param_userid = int(txt[13:])
                username_str = self.users.getUsername(param_userid)
                current_feedback = self.users.getFeedback(param_userid)
                if current_feedback:
                    feedback_str = "\n\n".join(current_feedback)
                    self.sendRawMessage(cid, "@%s:\n%s\n\n/replyToFeedback%d" % (username_str, feedback_str, param_userid))
                else:
                    self.sendMessage(cid, "Kein Feedback vorhanden")
                    
                    
            elif admin and txt.startswith("/replytofeedback"):
                m = re.match("/replytofeedback(\d+)", txt_strip, flags=re.MULTILINE|re.IGNORECASE)
                if m:
                    param_userid = int(m.group(1))
                    tosend = txt_strip[m.end():]
                    if len(tosend):
                        print(param_userid)
                        
                        self.sendRawMessage(param_userid, tosend+"\n\nIf you'd like to reply to this message please include the hashtag #feedback")
                        self.sendMessage(cid, "Sent!")
                    else:
                        self.sendMessage(cid, "Falsches Format: Kein Text")
                else:
                    self.sendMessage(cid, "Falsches Format: Keine ID")
                    
                
            elif admin and txt.startswith("/askforfeedback"):
                param_userid = int(txt[15:])
                
                try:
                    self.sendMessage(param_userid, "Hi again,\n\nI was wondering if you'd like to leave some #feedback.\n"+
                                                   "I would really appreciate it :face_blowing_a_kiss:\n\n"+
                                                   "Just send me a message with the tag #feedback and I'll make sure to forward it to the development team."+
                                                   "These boys and girls speak %s" % self._flags(":<gb>::<es>::<de>::<fr>::<il>::<no>:"), 
                                                   reply_markup=telepot.namedtuple.ForceReply(), disable_notification=True)
                    self.sendMessage(cid, "Sent!")
                except Exception as e:
                    self.sendMessage(cid, "Could not ask for feedback:\n```%s```" % str(e), parse_mode="Markdown")

            elif admin and '/me' == txt:
                self.sendMessage(cid, str(uid))

                

            elif "/start" == txt:
                self.sendMessage(cid,
                                 self.s.s("Das ist ein Bot für Informationen von [openmensa.org](https://openmensa.org/)\n\nBrauchst du Hilfe?"),
                                 parse_mode="Markdown",
                                 reply_markup=self._inlineKeyBoardYesNo((self.s.s("Ja"), "/help"), (self.s.s("Nein"),"/foobar"), ("English","/startenglish")))
                                 
            elif "/startenglish" == txt:
                self.users.setLanguage(uid, "English")
                self.speak.setLanguage(self.users.getLanguage(uid, self.speak.getDefaultLanguage()))
                self.sendMessage(cid, "Sure. Unfortunately, openmensa.org supports only one language per canteen and that's usually German, so I won't be able to send you menus in English.\n\nOh, and take a look at this:\nhttps://www.duolingo.com/comment/5707989/Why-you-should-learn-German")
                self.sendMessage(cid,
                                 self.s.s("Das ist ein Bot für Informationen von [openmensa.org](https://openmensa.org/)\n\nBrauchst du Hilfe?"),
                                 parse_mode="Markdown",
                                 reply_markup=self._inlineKeyBoardYesNo((self.s.s("Ja"), "/help"), (self.s.s("Nein"),"/foobar"), ("Deutsch","/deutsch")))

                                 
                                 
            elif "/help" == txt or "help" == txt or "hilfe" == txt:
                self.sendMessage(cid,
                                 self.s.s("Sende mir einfach deine aktuelle Position oder schreibe mir den Namen deiner Stadt\n") +"\n" +
                                 self.s.s("Andere Befehle:\n") +"\n" +
                                 self.s.s("/mensa{id} oder /heute{id}: Speiseplan anzeigen\n")+"\n" +
                                 self.s.s("/morgen{id} Speiseplan für folgenden Tag anzeigen\n")+"\n" +
                                 self.s.s("/map{id} Wegbeschreibung\n")+"\n" +
                                 self.s.s("/finde {name} Finde Mensen\n")+"\n" +
                                 self.s.s("/merke{id} Mensa als Favorit speichern\n")+"\n" +
                                 self.s.s("/vergiss{id} Favorit entfernen\n")+"\n" +
                                 self.s.s("/favoriten Zeige alle mit /merke gespeicherten Mensen\n")+"\n" +
                                 self.s.s("/push Pushbenachrichtigungen aktivieren. Du erhälst automatische den heutigen Speiseplan deiner Favoriten geschickt.\n") +"\n" +
                                 self.s.s("/push _hh:mm_ um die Uhrzeit für die Benachrichtigungen festzulegen.\n")+"\n" +
                                 self.s.s("/pushSilently Benachrichtigungston für die Speisepläne ausschalten.\n") +"\n" +
                                 self.s.s("/pushLoudly Benachrichtigungston für die Speisepläne einschalten.\n") +"\n" +
                                 self.s.s("/disablePush Pushbenachrichtigungen wieder ausschalten.\n")+"\n" +
                                 self.s.s("/enableEmojis Emojis in Speiseplänen anzeigen\n")+"\n" +
                                 self.s.s("/disableEmojis Keine Emojis in Speiseplänen anzeigen\n")+"\n" +
                                 self.s.s("/off Benachrichtigungen ausschalten und alle auf dem Server gespeicherten Daten löschen\n")+"\n" +
                                 self.s.s("/feedback Hinterlass dem Entwicklerteam eine Nachricht."))
                """
help - Hilfe
hilfe - Hilfe
feedback - Leave me a note
english - English
german - Deutsch
deutsch - Deutsch
find - Suchbegriff. Finde Mensen
finde - Suchbegriff. Finde Mensen
map - MensaID. Wegbeschreibung zur Mensa
karte - MensaID. Wegbeschreibung zur Mensa
merke - MensaID. Mensa als Favorit speichern
vergiss - MensaID. Favorit entfernen
mensa - MensaID. Speiseplan anzeigen
heute - MensaID. Speiseplan anzeigen
morgen - MensaID. Speiseplan für folgenden Tag
montag - Speiseplan für letzten Favorit
dienstag - Speiseplan für letzten Favorit
mittwoch - Speiseplan für letzten Favorit
donnerstag - Speiseplan für letzten Favorit
freitag - Speiseplan für letzten Favorit
samstag - Speiseplan für letzten Favorit
sonntag - Speiseplan für letzten Favorit
mensanext - MensaID. Speiseplan für folgenden Tag
favoriten - Zeige gespeicherte Mensen
push - hh:mm Benachrichtigungen aktivieren
pushsilently - Benachrichtigungston ausschalten
pushloudly - Benachrichtigungston einschalten
disablepush - Pushbenachrichtigungen auszuschalten
pushoff - Pushbenachrichtigungen auszuschalten
enableemojis - Emojis in Speiseplänen
disableemojis - kein Emojis in Speiseplänen
emojison - Emojis in Speiseplänen
emojisoff - kein Emojis in Speiseplänen
off - Account löschen, Benachrichtigungen ausschalten und gespeicherte Daten löschen
"""


            elif "/english" == txt or "english" == txt:
                self.users.setLanguage(uid, "English")
                self.speak.setLanguage(self.users.getLanguage(uid, self.speak.getDefaultLanguage()))
                self.sendMessage(cid, "Sure. Unfortunately, openmensa.org supports only one language per canteen and that's usually German, so I won't be able to send you menus in English.\n\nOh, and take a look at this:\nhttps://www.duolingo.com/comment/5707989/Why-you-should-learn-German")
                
            elif "/deutsch" == txt or "deutsch" == txt or "/german" == txt  or "german" == txt:
                self.users.setLanguage(uid, "Deutsch")
                self.speak.setLanguage(self.users.getLanguage(uid, self.speak.getDefaultLanguage()))
                self.sendMessage(cid, "Man spricht Deutsh")
                
            elif "/foobar" == txt:
                self.deleteMessage(msg)
                
            elif txt == "feedback" or "/feedback" in txt or "#feedback" in txt or "# feedback" in txt or ("reply_to_message" in msg and "text" in msg["reply_to_message"] and "#feedback" in msg["reply_to_message"]["text"]):
                if txt == "feedback" or txt[1:] == "feedback":
                    self.sendMessage(cid, self.s.s("Sende mir einfach eine Nachricht mit dem Tag #feedback zum Beispiel so:") + "\n\n`" +
                                          self.s.s("Euer Bot ist ganz doof #feedback") + "`\n\n" +
                                          self.s.s("Die Nachricht wird dann gespeichert und das Entwicklerteam schaut sie sich irgendwann an, vielleicht kontaktieren wir dich auch.") + "\n" + 
                                          self.s.s("Du kannst jederzeit alle deine persönlichen Daten inklusiv deines Feedbacks mit /off vom Server löschen."), parse_mode='Markdown')
                    current_feedback = self.users.getFeedback(uid)
                    if current_feedback:
                        self.sendMessage(cid, self.s.s("Dein bisheriges Feedback:"))
                        self.sendRawMessage(cid, "\n\n".join(current_feedback))
                    
                else:
                    self.users.saveFeedback(uid, txt_strip)
                    self.sendMessage(cid, ":OK_button::COOL_button: " + self.s.success(self.s.s("gespeichert")) + " :love_letter:")

            elif txt in ["what's up", "what's up?"]:
                self.sendMessage(cid, "a preposition")

            elif txt in ["was läuft?", "wie gehts?", "wie geht's?", "wie geht es dir", "wie geht es dir?"]:
                self.sendMessage(cid, "Läuft.")

            elif txt in ["was geht?", "was geht"]:
                self.sendMessage(cid, "Ja, geht so.")

            elif "sup" == txt or "sup?" == txt:
                self.sendMessage(cid, "gas prices")

            elif self._isEmoji(txt, [":cat:", ":cat_face:"]):
                self.sendMessage(cid, "Dachhasenbraten? Das ist doch verboten...")
                
            elif self._isEmoji(txt, [":camel:", ":two-hump_camel:"]):
                self.sendRawMessage(cid, "https://kamelrechner.eu")
                
            elif self._isEmoji(txt, ":panda_face:"):
                self.sendRawMessage(cid, "http://zoo.sandiegozoo.org/cams/panda-cam")       

            elif self._isEmoji(txt, [":kiss_mark:", ":face_blowing_a_kiss:", ":smiling_face_with_heart-eyes:"]):
                self.sendMessage(cid, ":face_blowing_a_kiss:")
                
            elif self._isEmoji(txt, [":grinning_face:", ":smiling_face_with_open_mouth:", ":smiling_face_with_open_mouth_&_smiling_eyes:", ":grinning_face_with_smiling_eyes:", 
                                     ":smiling_face_with_open_mouth_&_closed_eyes:", ":slightly_smiling_face:", ":smiling_face_with_smiling_eyes:", ":winking_face:"]):
                self.sendRawMessage(cid, "https://www.youtube.com/watch?v=OeowI8_J7ck")   

            elif self._hasEmoji(txt, [":see-no-evil_monkey:", ":hear-no-evil_monkey:", ":speak-no-evil_monkey:", ":monkey:", ":monkey_face:", ":gorilla:"]):
                self.sendMessage(cid, ':face_screaming_in_fear:\nhttp://wwf.panda.org/what_we_do/endangered_species/great_apes/gorillas/threats/')
                

            elif txt in ["hello","hallo","good day","hey","hi","hei","שלום","shalom","hola","guten tag","guten morgen","guten abend"]:
                self.sendMessage(cid, self.speak.hello())

            elif "/keyboard" == txt:
                self.sendKeyboard(cid)

            elif "/time" == txt:
                self.sendMessage(cid, self.timeNow().strftime("%x %X"))
                
            elif "/off" == txt:
                self.users.deleteUser(uid)
                self.sendMessage(cid, self.s.s("*Account gelöscht* :confused_face:\n\nAlle persönlichen Daten auf meinem Server wurden entfernt."), parse_mode="Markdown")
                
            elif "/mensa" == txt or "/mensa" == txt or "/heute" == txt or "/today" == txt:
                canteenid = 279
                favorites = self.users.getFavorites(uid)
                if len(favorites) > 0:
                    canteenid = favorites.pop()
                elif self.users.getLastCanteen(uid) is not None:
                    canteenid = self.users.getLastCanteen(uid)

                self.users.setLastCanteen(uid, canteenid)
                self.sendMensaMeals(cid, canteenid=canteenid)

            elif "/morgen" == txt or "/tomorrow" == txt:
                canteenid = 279
                favorites = self.users.getFavorites(uid)
                if len(favorites) > 0:
                    canteenid = favorites.pop()
                elif self.users.getLastCanteen(uid) is not None:
                    canteenid = self.users.getLastCanteen(uid)

                self.users.setLastCanteen(uid, canteenid)
                self.sendMensaMeals(cid, canteenid=canteenid, offsetDays=1)

            elif txt in self.weekdays_lower or (txt[0] == "/" and txt[1:] in self.weekdays_lower):
                canteenid = 279
                favorites = self.users.getFavorites(uid)
                if len(favorites) > 0:
                    canteenid = favorites.pop()
                elif self.users.getLastCanteen(uid) is not None:
                    canteenid = self.users.getLastCanteen(uid)

                if txt[0] == "/":
                    index = self.weekdays_lower.index(txt[1:])
                else:
                    index = self.weekdays_lower.index(txt)
                
                now = self.timeNow()
                today = now.date().weekday()
                if today > index:
                    daysFromToday = 7 + index - today
                else:
                    daysFromToday = index - today
                day = now + datetime.timedelta(days=daysFromToday)
                at_day = day.strftime("%Y-%m-%d")

                self.users.setLastCanteen(uid, canteenid)
                self.sendMensaMeals(cid, canteenid=canteenid, at_day=at_day)


            elif "/favoriten" == txt or "/favorites" == txt or "/favourites" == txt:
                favorites = self.users.getFavorites(uid)
                if len(favorites) == 0:
                    self.sendMessage(cid, self.s.s("Du hast noch keine Favoriten.\n")+self.speak.advice(self.s.s("setze Favoriten mit /merke _id_\noder mit dem :red_heart: unter dem Speiseplan")), parse_mode="Markdown")
                else:
                    favs = "\n".join(["/mensa%d" % i for i in favorites])
                    self.sendMessage(cid, self.s.s("Deine Favoriten:\n%s\n\nUm eine Mensa zu entfernen, klick auf den Mensa Link und dann auf das :broken_heart:") % favs, parse_mode="Markdown")



            elif "/push" == txt:
                if self.users.getPush(uid):
                    # Show information
                    at_time = self.users.getPush(uid)
                    
                    in_h, in_m, in_s = self._timeTo(at_time)
                    remaining = self._formatTimeRemaining(in_h, in_m, in_s)
                    
                    silent = self.users.isPushSilent(uid)
                    
                    text = self.s.s("Pushbenachrichtigungen aktiviert. Du erhälst um %s Uhr ") % at_time.strftime("%X")
                    text += self.s.s("automatisch den Speiseplan deiner Favoriten geschickt.\n") + "\n"
                    if silent:
                        text += self.s.s("Der Benachrichtigungston ist ausgeschaltet.\n")
                        text += self.s.s("/pushLoudly um den Benachrichtigungston für die Speisepläne einzuschalten.\n") + "\n"
                    else:
                        text += self.s.s("Der Benachrichtigungston ist eingeschaltet.\n")
                        text += self.s.s("/pushSilently um den Benachrichtigungston für die Speisepläne auszuschalten.\n") + "\n"
                    text += self.s.s("/favoriten um deine aktuellen Favoriten anzusehen.\n")
                    text += self.s.s("/push _hh:mm_ um die Uhrzeit für die Benachrichtigungen festzulegen.\n")
                    text += self.s.s("/disablepush um die Pushbenachrichtigungen wieder auszuschalten.\n") + "\n"
                    text += self.s.s("Nächste Nachricht in ungefähr %s.") % remaining
                else:
                    # Enable Push at random time
                    h = 10
                    m = random.randint(0,59)
                    at_time = datetime.time(h, m)
                    
                    self.users.enablePush(uid, at_time)
                    
                    in_h, in_m, in_s = self._timeTo(at_time)
                    remaining = self._formatTimeRemaining(in_h, in_m, in_s)

                    text = self.s.s("Pushbenachrichtigungen aktiviert. Du erhälst um %d:%02d Uhr ") % (h,m)
                    text += self.s.s("automatisch den Speiseplan deiner Favoriten geschickt.\n") + "\n"
                    text += self.s.s("Folgende Befehle könnten nützlich sein:") + "\n"
                    text += self.s.s("/favoriten um deine aktuellen Favoriten anzusehen.\n")
                    text += self.s.s("/pushSilently um den Benachrichtigungston für die Speisepläne auszuschalten.\n")
                    text += self.s.s("/pushLoudly um den Benachrichtigungston für die Speisepläne einzuschalten.\n")
                    text += self.s.s("/push _hh:mm_ um die Uhrzeit für die Benachrichtigungen festzulegen.\n")
                    text += self.s.s("/disablepush um die Pushbenachrichtigungen wieder auszuschalten.\n") + "\n"
                    text += self.s.s("Nächste Nachricht in ungefähr %s.") % remaining
                
                self.sendMessage(cid, text, parse_mode="Markdown")
                
                favorites = self.users.getFavorites(uid)
                if len(favorites) == 0:
                    self.sendMessage(cid, self.s.s("Du hast noch keine Favoriten.\n")+self.speak.advice(self.s.s("setze Favoriten mit /merke _id_\noder mit dem :red_heart: unter dem Speiseplan")), parse_mode="Markdown")
                

            elif re.search("/push\s*(\d+)", txt):
                # /push HH:mm
                # /push HH

                m = re.findall("(\d+)", txt)
                at_time = datetime.time(*[int(i) for i in m[0:4]])

                self.users.enablePush(uid, at_time)


                in_h, in_m, in_s = self._timeTo(at_time)
                remaining = self._formatTimeRemaining(in_h, in_m, in_s)

                text = self.s.s("Pushbenachrichtigungen aktiviert. Du erhälst um %s Uhr ") % at_time.strftime("%X")
                text += self.s.s("automatisch den Speiseplan deiner Favoriten geschickt.\n") + "\n"
                text += self.s.s("Folgende Befehle könnten nützlich sein:") + "\n"
                text += self.s.s("/favoriten um deine aktuellen Favoriten anzusehen.\n")
                text += self.s.s("/pushSilently um den Benachrichtigungston für die Speisepläne auszuschalten.\n")
                text += self.s.s("/pushLoudly um den Benachrichtigungston für die Speisepläne einzuschalten.\n")
                text += self.s.s("/push _hh:mm_ um die Uhrzeit für die Benachrichtigungen festzulegen.\n")
                text += self.s.s("/disablepush um die Pushbenachrichtigungen wieder auszuschalten.\n") + "\n"
                text += self.s.s("Nächste Nachricht in ungefähr %s.") % remaining

                self.sendMessage(cid, text, parse_mode="Markdown")
                
                favorites = self.users.getFavorites(uid)
                if len(favorites) == 0:
                    self.sendMessage(cid, self.s.s("Du hast noch keine Favoriten.\n")+self.speak.advice(self.s.s("setze Favoriten mit /merke _id_\noder mit dem :red_heart: unter dem Speiseplan")), parse_mode="Markdown")

            elif "/disablepush" == txt or "/pushoff" == txt:
                self.users.disablePush(uid)

                self.sendMessage(cid, emoji.emojize(self.s.s("Pushbenachrichtigungen deaktiviert :neutral_face:")), parse_mode="Markdown")

            elif "/pushsilent" == txt or "/pushsilently" == txt or self._isEmoji(txt, ":bell_with_slash:"):
                self.users.enablePushSilent(uid)

                self.sendMessage(cid, emoji.emojize(self.s.s(":bell_with_slash: Benachrichtigungston für Pushbenachrichtigungen deaktiviert :zipper-mouth_face:")), parse_mode="Markdown")

            elif "/pushloud" == txt or "/pushloudly" == txt or "/pushnoisy" == txt or "/pushnoisily" == txt or self._isEmoji(txt, ":bell:"):
                self.users.disablePushSilent(uid)

                self.sendMessage(cid, emoji.emojize(self.s.s(":bell: Benachrichtigungston für Pushbenachrichtigungen aktiviert")), parse_mode="Markdown")

            elif "/enableemojis" == txt or "/emojison" == txt:
                self.users.enableEmojis(uid)

                self.sendMessage(cid, emoji.emojize(self.s.s(":thumbs_up: Emojis in Speiseplänen aktiviert :smiling_cat_face_with_heart-eyes:")), parse_mode="Markdown")

            elif "/disableemojis" == txt or "/emojisoff" == txt:
                self.users.disableEmojis(uid)

                self.sendMessage(cid, emoji.emojize(self.s.s("Emojis in Speiseplänen deaktiviert :fearful_face:")), parse_mode="Markdown")


            elif re.search("/?(map|karte)\s*(\d+)", txt):
                # /map$id
                m = re.search("/?(map|karte)\s*(\d+)", txt)
                canteenid = int(m.group(2))

                mensa = self.openmensa.getMensa(canteenid=canteenid)
                
                address = ""

                if not mensa:
                    self.sendMessage(cid, self.speak.apologize(self.s.s("die Mensa %d kann ich nicht finden") % canteenid))
                elif not "coordinates" in mensa:
                    if not "address" in mensa:
                        self.sendMessage(cid, self.speak.apologize(self.s.s("für %s habe ich keine genaue Position oder Adresse") % mensa["name"]))
                    else:
                        address = mensa["address"]
                        googlemaps = "http://maps.google.com/maps?q=%s&z=15" % urllib.parse.quote_plus(address);
                        self.sendMessage(cid, "%s\n[%s](%s)" % (mensa["name"], address, googlemaps), parse_mode="Markdown")
                else:
                    if "address" in mensa:
                        address = mensa["address"]
                        #googlemaps = "http://maps.google.com/maps?q=%s&z=15" % urllib.parse.quote_plus(address);
                        #self.sendMessage(cid, "[%s](%s)" % (address, googlemaps), parse_mode="Markdown")
                    self.bot.sendVenue(cid, latitude=mensa["coordinates"][0], longitude=mensa["coordinates"][1], title=mensa["name"], address=address)


            elif re.search("/?mensa\s*(\d+)", txt) or re.search("/?heute\s*(\d+)", txt):
                # /mensa$id /heute$id
                m = [int(x) for x in re.findall("(\d+)", txt)]

                for canteenid in m:
                    self.sendMensaMeals(cid, canteenid=canteenid)


            elif re.search("/?mensanext\s*(\d+)[_|\s]+(\d+)", txt):
                # /mensaNext $id $offset
                m = [(int(pair[0]), int(pair[1])) for pair in re.findall("(\d+)[_|\s+](\d+)", txt) ]

                for canteenid, offsetDays in m:
                    self.sendMensaMeals(cid, canteenid=canteenid, offsetDays=offsetDays)

                self.users.setLastCanteen(uid, canteenid)

            elif re.search("/?mensanext\s*(\d+)", txt) or re.search("/?morgen\s*(\d+)", txt):
                # /mensaNext$id
                m = [int(x) for x in re.findall("(\d+)", txt)]

                for canteenid in m:
                    self.sendMensaMeals(cid, canteenid=canteenid, offsetDays=1)

                self.users.setLastCanteen(uid, canteenid)

            elif re.search("/?m(?:ensa|\s)\s*(\w+)", txt):
                # /mensa$shortname
                m = re.search("/?m(?:ensa|\s)\s*(\w+)", txt)

                canteenid = self.openmensa.getIdFromShortName(m.group(1))
                if canteenid != False:
                    self.users.setLastCanteen(uid, canteenid)
                    self.sendMensaMeals(cid, canteenid=canteenid)
                else:
                    q = re.sub("/\w+\s*","", txt).strip()
                    self.sendMensaFind(cid, query=q)

            elif re.search("/?finde? (.*)", txt):
                # /find name
                m = re.search("/?finde? (.*)", txt)

                self.sendMensaFind(cid, query=m.group(1))

            elif re.search("/?merke\s*(\d+)", txt):
                # /merke$id
                m = re.search("/?merke\s*(\d+)", txt)

                canteenid = int(m.group(1))

                shortname = self.openmensa.getShortName(canteenid)
                if shortname != False:

                    self.users.saveFavorite(uid, canteenid)

                    """
                    buttons = []
                    for canteenid in self.users.getFavorites(uid):
                        buttons.append(telepot.namedtuple.KeyboardButton(text="m %s" % self.openmensa.getShortName(canteenid)))
                    reply_markup=self._keyBoard(buttons)"""
                    self.sendMessage(cid, self.speak.success(self.s.s("gespeichert")))
                else:
                    self.sendMessage(cid, self.speak.apologize(self.s.s("die Mensa %d kann ich nicht finden") % canteenid))

            elif re.search("/?vergiss\s*(\d+)", txt):
                # /vergiss$id
                m = re.search("/?vergiss\s*(\d+)", txt)

                canteenid = int(m.group(1))

                self.users.removeFavorite(uid, canteenid)

                self.sendMessage(cid,
                                 self.speak.success(self.s.s("entfernt")))



            elif re.search("^\s*(\d+)\s*$", txt):
                # $id
                m = re.search("\d+", txt)

                canteenid = int(m.group(0))
                self.sendMensaMeals(cid, canteenid=canteenid)

                self.users.setLastCanteen(uid, canteenid)
                
                
            elif txt.startswith("/"):
                # Unkown command. Remove command and serach for mensa
                q = re.sub("/\w+\s*","", txt).strip()
                self.sendMensaFind(cid, query=q)

            elif len(txt) > 2:
                self.sendMensaFind(cid, query=txt)

            else:
                self.sendMessage(cid, self.speak.apologize(self.s.s("das verstehe ich nicht")))


        elif content_type == "location":
            lat, lng = msg["location"]["latitude"], msg["location"]["longitude"]

            self.sendMensasNear(cid, lat, lng)
        
        
        else:
            
            self.sendMessage(cid, (self.s.s("Wissenschaftler haben herausgefunden, dass es sich um ein %s handelt.\n") % content_type) + self.speak.apologize(self.s.s("was soll ich damit?!")))


        if callbackAnswered == False:
            self.bot.answerCallbackQuery(query_id)

    def _handleInlineCallbackQuery(self, msg):
        query_id, uid, data = telepot.glance(msg, flavor='callback_query')
        txt = data.lower()
        
        inline_message_id = msg["inline_message_id"]
        
        self.speak.setLanguage(self.users.getLanguage(uid, self.speak.getDefaultLanguage()))

        self.weekdays = [self.s.s("Montag"),self.s.s("Dienstag"),self.s.s("Mittwoch"),self.s.s("Donnerstag"),self.s.s("Freitag"),self.s.s("Samstag"),self.s.s("Sonntag")]
        self.weekdays_lower = [self.s.s("montag"),self.s.s("dienstag"),self.s.s("mittwoch"),self.s.s("donnerstag"),self.s.s("freitag"),self.s.s("samstag"),self.s.s("sonntag")]
        self.todayWord = self.s.s("Heute")
        self.tomorrowWord = self.s.s("Morgen")
        
        
        def getInlineInlineKeyBoard(canteenid, offsetDays=0):
            backButton = (":left_arrow:",  "/mensaNextInline%d_%d" % (canteenid, offsetDays - 1))
            nextButton = (":right_arrow:", "/mensaNextInline%d_%d" % (canteenid, offsetDays + 1))
            
            if offsetDays < 1:
                return self._inlineKeyBoard(nextButton)
            
            return self._inlineKeyBoard(backButton, nextButton)
        
        if re.search("/mensainline(\d+)", txt):
            # /mensaInline$id
            m = re.search("(\d+)", txt)
            canteenid = int(m.group(1))

            ret = self.getSendMensaMealsMessage(uid, canteenid)
            
            self.bot.editMessageText(
                msg_identifier = inline_message_id,
                text=emoji.emojize(ret["text"]),
                parse_mode=ret["parse_mode"],
                reply_markup=getInlineInlineKeyBoard(canteenid, 0))
            
        elif re.search("/mensanextinline(\d+)_(\d+)", txt):
            # /mensaNextInline$id_$offset
            m = re.search("(\d+)_(\d+)", txt)
            canteenid = int(m.group(1))
            offsetDays = int(m.group(2))
            
            ret = self.getSendMensaMealsMessage(uid, canteenid, offsetDays=offsetDays)
            
            self.bot.editMessageText(
                msg_identifier = inline_message_id,
                text=emoji.emojize(ret["text"]),
                parse_mode=ret["parse_mode"],
                reply_markup=getInlineInlineKeyBoard(canteenid, offsetDays))
                
        elif re.search("/mensanextinline(\d+)", txt):
            # /mensaNextInline$id
            offsetDays = 1
            m = re.search("(\d+)", txt)
            canteenid = int(m.group(1))
            
            ret = self.getSendMensaMealsMessage(uid, canteenid, offsetDays=offsetDays)
            
            self.bot.editMessageText(
                msg_identifier = inline_message_id,
                text=emoji.emojize(ret["text"]),
                parse_mode=ret["parse_mode"],
                reply_markup=getInlineInlineKeyBoard(canteenid, offsetDays))
            
        else:
            print("Unkown InlineCallbackQuery: data=%s" % data)
                
                
        self.bot.answerCallbackQuery(query_id)

    def _handleCallbackQuery(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        
        """
        try:
            pprint(msg)
        except:
            pass"""

        if "message" in msg:
            message_id = msg["message"]["message_id"]

            message = msg["message"]
            message["text"] = query_data
            message["from"] = msg["from"]

            self._handleMessage(message, query_id)
            
        elif "inline_message_id" in msg:
            self._handleInlineCallbackQuery(msg)
            


    def _handleInlineQuery(self, msg):

        def compute():
            query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')

            uid = from_id
            uname = None
            uname_str = ""
            if "from" in msg and "username" in msg["from"]:
                uname = msg["from"]["username"]
                self.users.addUser(uid, uname)
                uname_str = uname.encode('unicode-escape').decode('ascii')
            else:
                uname_str = "<unknown>"
                
            print("Inline-@%s: %s" % (uname_str, emoji.demojize(query_string).encode('unicode-escape').decode('ascii')))
            
            
            self.speak.setLanguage(self.users.getLanguage(uid, self.speak.getDefaultLanguage()))

            self.weekdays = [self.s.s("Montag"),self.s.s("Dienstag"),self.s.s("Mittwoch"),self.s.s("Donnerstag"),self.s.s("Freitag"),self.s.s("Samstag"),self.s.s("Sonntag")]
            self.weekdays_lower = [self.s.s("montag"),self.s.s("dienstag"),self.s.s("mittwoch"),self.s.s("donnerstag"),self.s.s("freitag"),self.s.s("samstag"),self.s.s("sonntag")]
            self.todayWord = self.s.s("Heute")
            self.tomorrowWord = self.s.s("Morgen")
            
            
            
            def getInlineInlineKeyBoard(canteenid, reloadButton=False, nextButton=True, backButton=False, offsetDays=None):
                buttons = []
                if backButton and offsetDays is not None:
                    backButton = (":left_arrow:",  "/mensaNextInline%d_%d" % (canteenid, offsetDays - 1))
                    buttons.append(backButton)
                
                if reloadButton:
                    if offsetDays is not None:
                        reloadButton = (":anticlockwise_arrows_button:",  "/mensaNextInline%d_%d" % (canteenid, offsetDays))
                    else:
                        reloadButton = (":anticlockwise_arrows_button:", "/mensaInline%d" % canteenid)
                    buttons.append(reloadButton)
                
                if nextButton:
                    if offsetDays is not None:
                        nextButton = (":right_arrow:",  "/mensaNextInline%d_%d" % (canteenid, offsetDays + 1))
                    else:
                        nextButton = (":right_arrow:", "/mensaNextInline%d" % canteenid)
                    buttons.append(nextButton)
                
                return self._inlineKeyBoard(*buttons)
            
            

            Article = telepot.namedtuple.InlineQueryResultArticle
            TextMessageContent = telepot.namedtuple.InputTextMessageContent

            if re.search("^\s*(\d+)\s*$", query_string):
                m = re.search("^\s*(\d+)\s*", query_string)
                canteenid = int(m.group(1))
                mensa = self.openmensa.getMensa(canteenid)
                if mensa is None:
                    articles = [Article(
                                    id='canteen%d' % canteenid,
                                    title=self.s.s("Kein Ergebnis"),
                                    description=self.s.s("Nichts gefunden zu id=%d") % canteenid,
                                    input_message_content=TextMessageContent(
                                        message_text=self.speak.apologize(self.s.s("bist du sicher, dass die ID %d korrekt ist") % canteenid)
                                    )
                               )]
                else:
                    self.users.setLastCanteen(uid, canteenid)
                    preview, text = self.getMensaMealsFormatted(canteenid, uid=uid)
                    articles = [Article(
                                    id='canteenMeals%d' % canteenid,
                                    title=mensa["name"],
                                    description=emoji.emojize(preview),
                                    reply_markup=getInlineInlineKeyBoard(canteenid),
                                    input_message_content=TextMessageContent(
                                        message_text=emoji.emojize(text),
                                        parse_mode='Markdown'
                                    )
                               )]


            elif len(query_string) > 0:
                mensas = self.openmensa.findMensaByString(query_string)

                if len(mensas) == 1:
                    mensa = mensas[0]
                    self.users.setLastCanteen(uid, mensa["id"])
                    preview, text = self.getMensaMealsFormatted(mensa["id"], uid=uid)
                    articles = [ Article(
                        id='canteenMeals%d' % mensa["id"],
                        title=mensa["name"],
                        description=emoji.emojize(preview),
                        reply_markup=getInlineInlineKeyBoard(mensa["id"]),
                        url='https://openmensa.org/c/%d' % mensa["id"],
                        input_message_content=TextMessageContent(
                            message_text=emoji.emojize(text),
                            parse_mode='Markdown'
                        )
                    ) ]
                elif len(mensas) > 0 and len(mensas) < 50:
                    articles = []
                    for mensa in mensas:

                        cached = self.openmensa.getNextMealIfCached(mensa["id"])
                        if cached is None:
                            # Do not show meals. Fetching them would be to expensive on openmensa.org server
                            text = self.speak.apologize(self.s.s("Daten veraltet!"))+" "
                            text += self.s.s("Klick unten auf den :anticlockwise_arrows_button: um den aktuellen Plan zu erhalten")+"\n\n"
                            text += self.s.s("Oder gib einen spezifischen Suchbegriff ein, damit du nur ein Ergebnis erhältst, dann wird der Speiseplan direkt angezeigt")
                            text += self.s.s("\n\nBeispiel:\n@OpenMensaRobot %s\n\nOder gibt die ID der Mensa an:\n@OpenMensaRobot %d") % (self.openmensa.getShortName(mensa["id"]), mensa["id"])
                            
                            a = Article(
                                id='canteenResult%d' % mensa["id"],
                                title=mensa["name"],
                                description=mensa["city"],
                                reply_markup=getInlineInlineKeyBoard(mensa["id"], reloadButton=True, nextButton=False),
                                url='https://openmensa.org/c/%d' % mensa["id"],
                                input_message_content=TextMessageContent(
                                    message_text=emoji.emojize(text),
                                    parse_mode='Markdown'
                                    )
                            )
                            articles.append(a)
                        else:
                            # We're lucky, the meals were in the cache:
                            day, meals, ret = cached
                            preview, text = self.getMensaMealsFormatted(mensa["id"], uid=uid)
                            a = Article(
                                id='canteenMeals%d' % mensa["id"],
                                title=mensa["name"],
                                description=emoji.emojize(preview),
                                reply_markup=getInlineInlineKeyBoard(mensa["id"]),
                                url='https://openmensa.org/c/%d' % mensa["id"],
                                input_message_content=TextMessageContent(
                                    message_text=emoji.emojize(text),
                                    parse_mode='Markdown'
                                )
                            )
                            articles.append(a)

                elif len(mensas) == 0:
                    articles = [Article(
                        id='noResults',
                        title=self.s.s("Keine Ergebnisse"),
                        description=self.s.s("Bitte ändere den Suchbegriff"),
                        input_message_content=TextMessageContent(
                            message_text=self.speak.apologize(self.s.s("keine Ergebnisse. Bitte ändere den Suchbegriff")),
                            parse_mode='Markdown'
                        )
                    )]
                else:
                    articles = [Article(
                        id='tooUnspecific',
                        title=self.s.s("Zu viele Ergebnisse"),
                        description="Bitte spezifiere den Suchbegriff",
                        input_message_content=TextMessageContent(
                            message_text=self.speak.apologize(self.s.s("zu viele Ergebnisse. Bitte spezifiere den Suchbegriff")),
                            parse_mode='Markdown'
                        )
                    )]

            else:
                articles = []
                canteenid = None
                favorites = self.users.getFavorites(uid)
                if len(favorites) > 0:
                    canteenid = favorites.pop()
                else:
                    canteenid = self.users.getLastCanteen(uid)

                if canteenid is not None:
                    day, meals, ret = self.openmensa.getNextMeal(canteenid)
                    mensa = self.openmensa.getMensa(canteenid)

                    if len(meals) == 0:
                        date = ""
                        if day is not None:
                            datetime_day = datetime.datetime.strptime(day, '%Y-%m-%d')
                            dateformat = self.s.dateFormat()
                            date = self.__formatDate(datetime_day, format=dateformat)
                        articles = [Article(
                                        id='canteen%d' % canteenid,
                                        title=mensa["name"],
                                        description=self.s.s("Geschlossen") + date,
                                        reply_markup=getInlineInlineKeyBoard(canteenid),
                                        input_message_content=TextMessageContent(
                                            message_text=self.speak.apologize(self.s.s("%s Nichts gefunden. Vielleicht ist die Mensa %s gerade geschlossen") % (date, mensa["name"]))
                                        )
                                   )]
                    else:
                        s = [
                            "_@OpenMensaRobot %d_" % canteenid,
                            "[%s](https://openmensa.org/c/%d)" % (day, canteenid) ]
                        last_cat = ""
                        for meal in meals:
                            t = ""
                            if meal["category"] != last_cat:
                                last_cat = meal["category"]
                                t += "\n*%s*:\n" % meal["category"].strip()
                            t += meal["name"].strip()
                            s.append(t)

                        preview = "%s..." % meals[0]["name"][0:100]
                        text = "\n".join(s)

                        articles = [Article(
                                        id='canteenMeals%d' % canteenid,
                                        title=mensa["name"],
                                        description=preview,
                                        reply_markup=getInlineInlineKeyBoard(canteenid),
                                        input_message_content=TextMessageContent(
                                            message_text=text,
                                            parse_mode='Markdown'
                                        )
                                   )]



            return articles

        self.answerer.answer(msg, compute)

        
    def stop(self):
        self.__stopFlag[0] = True

    def run(self, webhookURL):
        if "Running" in self.status:
            print("Already running")
            return self._webhook
        
        self.status += "Running"


        self.bot = telepot.Bot(mytoken.HTTP_TOKEN)
        self.answerer = telepot.helper.Answerer(self.bot)

        self._webhook = OrderedWebhook(self.bot, {
            'chat': self._handleMessage,
            'callback_query':self._handleCallbackQuery,
            'inline_query': self._handleInlineQuery
            })
        self._webhook.run_as_thread()
        self.bot.setWebhook(webhookURL)
            
            
            
        print("Running@"+webhookURL)
        print(emoji.demojize(str(self.bot.getMe())).encode('unicode-escape').decode('ascii'))

        if self.informStatusTo:
            try:
                self.sendMessage(self.informStatusTo, "Server started", disable_notification=True)
            except:
                print("Cannot send status messages to %s" % str(self.informStatusTo))
                pass
        
        return self._webhook

    def worker(self):
        if "Working" in self.status:
            print("Already working")
            return
        
        self.status += "Working"
        
        stopFlag = self.__stopFlag
        
        class MyWorker(threading.Thread):
             def __init__(self, myMensaBot):
                 super().__init__()
                 self.tosend_objs = []
                 self.__myMensaBot = myMensaBot

             def run(self):
                while True:
                    if stopFlag[0]:
                        break
                    new_objs = self.__myMensaBot.users.getPendingPushObjects(self.__myMensaBot.timeNow().time())
                    self.tosend_objs.extend(new_objs)

                    for i in range(min(len(self.tosend_objs), 20)):
                        obj = self.tosend_objs.pop(0)
                        print(obj)
                        uid = obj[0]
                        self.__myMensaBot.setLanguage(self.__myMensaBot.users.getLanguage(uid, self.__myMensaBot.speak.getDefaultLanguage()))
                        silent = self.__myMensaBot.users.isPushSilent(uid)
                        for canteenid in obj[1]:
                            day, meals, ret = self.__myMensaBot.openmensa.getNextMeal(canteenid)
                            if ret != False and len(meals) > 0 and day is not None and datetime.datetime.strptime(day, '%Y-%m-%d').date() == self.__myMensaBot.timeNow().date():
                                try:
                                    self.__myMensaBot.sendMensaMeals(uid, canteenid, disableNotification=silent)
                                except Exception as e:
                                    print("Could not send push message: %s" % str(e))
                    
                    
                    self.__myMensaBot.users.commitChanges() # Save users database to pickle file
                    time.sleep(20)
                    
                print("Stopped Worker thread")

        self.worker = MyWorker(self)
        self.worker.daemon = True
        self.worker.start()



