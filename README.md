# Vocabulary Analysis

When I was younger, a Psychology Professor came up to me and said something that I remember to this day. 
He said, "To bring the information from the unconscious level to the level of consciousness, it takes seven exposures on average."
I am not sure why I remember this, but it has impacted me to create the vocabulary suggesting algorithm years later. 
Recently, I have been trying to develop a system that would allow me to memorize vocabulary more efficiently since it was easy for me to learn a word but challenging to own it. 
Thus, I decided to test the hypothesis of the Psychology Professor and create an algorithm that would allow me to spend the least amount of time to "own" new vocabulary learned.

<br>  

# Purpose & Goal
- **The total time spent** learning new vocabulary is the key component of this project. Instead of spending too much time learning & remembering, the goal is to periodically expose each vocabulary to my brain a total of 7 times. There will be three notifications a day(morning, afternoon, and at night) suggesting five vocabualries each time. Also, when the vocabs are suggested via Slack message, I will spend less than 15 seconds relearning them. Thus, the ultimate goal is to spend less than a minute every day(including all three notifications) to own hundreds or even thousands of vocabulary in the future. 
- After the seven exposures, each vocabulary will be moved to another database where I will test myself whether or not I can create meaningful sentences and test my knowledge of the learned vocabs. Then, depending on my confidence level, I will rate each from 1 to 5 to further analyze the algorithm's efficiency.
    - ⭐️⭐️⭐️⭐️⭐️: Complete mastery of the vocab
    - ⭐️⭐️⭐️⭐: Need 1 or 2 more exposures to reach complete mastery
    - ⭐️⭐️⭐️: Know the meaning, but cannot effectively utilize in conversations
    - ⭐️⭐️: Understand the connotation
    - ⭐️: Unclear

<br>  
<br>  

# Algorithm Development Procedure
The code was relatively simple, but the procedure needed a little contemplation.
<br>  
### 1. Collect Vocabularies in [Notion database](https://andyhomepage.notion.site/Vocabularies-c97b642944854b44826d8a1ce73bc3da)
This process takes less than 10 seconds to record. 
I would simply go into the Notion application and type in the vocabulary I wish to learn.

### 2. Connect to Slack API
Connecting to Slack API allows to set up timed notifications for the exposures of the vocabularies. 

### 3. Write Smart (Vocabluary) Suggesting Algorithm 
These are some of the **conditions & procedures** when suggesting vocabularies:
- Sort the vocabularies with minimum counts(exposures) so that suggestions are not clustered
- Eliminate redundant or consecutive suggestions
- Suggest a total of 15 vocabularies a day divided into 3 sections: morning, afternoon, and night
- Add the number of exposure by one every time each vocabulary is exposed to my brain
- Update above changes to the Notion Vocabulary database
- Record the vocabulary input date and the date when I checked the memorization completed box for further analysis
