# INFO

In this file all skills and functions as well as examples on how to trigger them are listed, since the NLU model is not
fully trained due to the short working interval regarding the bachelor's thesis. Generally there are two parts in which
the interaction with RAINA can be divided:

1. Learning the BZfE Nutrition Pyramid
2. Tracking one's diet and nutrition on the fly by filling out the pyramid

You can test the most recent version of RAINA either via

1. Telegram: @tum_raina_bot  
   or
2. the RasaX Webchat (no check-ins): https://rasa.selectcode.io/guest/conversations/production/c46d18472dfe4f9eb21c50d334c526c6

## Teaching the Nutrition Pyramid

RAINA uses the nutrition pyramid as well as all educational information from the BZfE:  
https://www.bzfe.de/ernaehrung/die-ernaehrungspyramide/die-ernaehrungspyramide-eine-fuer-alle/

### Content

1. Initial message (Greeting user, providing main page of BZfE nutrition pyramid)
2. asking knowledge about the pyramid in general
3. asking knowledge about the colors in the pyramid
4. asking knowledge about the different icons in thy pyramid
5. asking knowledge about the portion sizes used
6. exercise to add a portion
7. exercise to ask for a pyramid
8. tell user he/she is ready to go

### Conversation Flow

The questions asked are yes/no questions and the answers are being implemented using telegram response-buttons to avoid
breaking out of the conversation. If the user understood the topic RAINA will praise their knowledge, if the user does
not understand the topic RAINA will briefly explain it, provide a link to the topic on the Website of the BZfE and
ask the next question


## Tracking the Diet

RAINA knows the following fields for sure, she will understand portions of:

- Getränke
- Obst
- Gemüse
- Kohlenhydrate
- Milchprodukte
- Fleisch
- Fett
- Öl
- Extras

(as well as some synonyms for each, defined in `data/nlu/synonyms.yml`)

### Supported functionality

1. Retrieve the pyramid for the current day  
   `Wie sieht die Pyramide heute aus?`  
   `Zeige mir meine Pyramide.`


2. Adding portions/marking fields as consumed RAINA understands numbers as Strings ("eine", "zwei", ...), Integers ("1"
   , "2", ...) and Floats in german spelling ("1,5", "3,141592")  
   `Ich habe eine Portion Wasser getrunken.`  
   `Ich habe eine Portion Obst gegessen.`  
   `Füge eine Portion Gemüse hinzu.`  
   `Eine Portion Extras mehr.`  
   `Füge 3 Portionen Wasser hinzu.`  
   `Füge 1,5 Portionen Milchprodukte hinzu.`


3. Removing portions/unmarking fields This works analogue to adding portions. Same field names and number recognition.  
   `Eine Portion Extras weniger.`  
   `Ziehe 3 Portionen Wasser ab.`  
   `Lösche 1,5 Portionen Milchprodukte.` 
  

4. Retrieve average pyramid for custom period of time  
   `Wie sieht die druchschnittliche Pyramide über die letzten 7 Tage aus?`  
   `Wie war meine Ernährung die letzten 14 Tage?`  
   `Zeige mir meine durchschnittliche Pyramide für die letzten 30 Tage.`  
   `Zeige mir meine Pyramide von 01.01.2021 bis 13.10.2021.`  


## Getting pyramids from the past  

You can get either specific discrete pyramids for exact dates or averages of the pyramids in a timespan.  

1. Retrieve pyramid for a specific day  
   `Wie sah meine pyramide gestern aus?`  
   `Wie sah meine Pyramide vor einer Woche aus?`  
   `Wie sah meine Pyramide am 01.01.2021 aus?`
  

2. Average pyramid over a given time span  
   `wie sieht meine durchschnittliche Pyramide der letzten 7 Tage aus?`  
   `wie sieht meine Pyramide von letzter Woche bis jetzt aus?`  
   `zeige mir meine durchschnittliche Pyramide für die letzten 30 Tage.`  
   `zeige mir meine Pyramide von 01.01.2021 bis 13.10.2021`    


## Weekly Overview and Reminders
There are three scheduled check-ins implemented: every morning at 8 a.m., every evening at 5 p.m. and every sunday
at 8 p.m.  
RAINA asks for the motivation in the morning, for self assessment of the current day at the evening and for self assessment
for the past week every sunday. The answers are mapped to a Likert-Scale and stored in the database.

To manually trigger a reminder, you can send the following intents directly to RAINA:  
1. `/EXTERNAL_send_morning_check_in`
2. `/EXTERNAL_send_evening_check_in`
3. `/EXTERNAL_send_weekly_check_in`