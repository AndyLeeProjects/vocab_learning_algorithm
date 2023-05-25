# Vocabulary Learning Algorithm

When I was younger, a Psychology Professor came up to me and said something that I remember to this day.
He said, "To bring the information from the unconscious level to the level of consciousness, it takes seven exposures on average."
I am not sure why I remember this, but it has impacted me to create the vocabulary suggesting algorithm years later.
Recently, I have been trying to develop a system that would allow me to memorize vocabulary more efficiently since it was easy for me to learn a word but challenging to own it.
Thus, I decided to test the hypothesis of the Psychology Professor and create an algorithm that would allow me to spend the least amount of time to "own" new vocabulary learned.

<br>  

# Purpose & Goal

- **The total time spent** learning new vocabulary is the key component of this project. Instead of spending too much time learning & remembering, the goal is to periodically expose each vocabulary to my brain a total of 7 times. There will be three notifications a day(morning, afternoon, and night) suggesting an appropriate number of vocabulary each time. Also, when the vocabs are notified via Slack, I will spend less than 1 minute relearning them. Thus, the ultimate goal is to spend less than 3 minutes every day(including all three notifications) to master hundreds or even thousands of vocabulary in the future.
- After the seven exposures, each vocabulary will be automatically moved to another database where I will test myself whether or not I can create meaningful sentences and test my knowledge of the learned vocabs. Then, depending on my confidence level, I will rate each from 1 to 5 to further analyze the algorithm's efficiency.
    - ⭐️⭐️⭐️⭐️⭐️: Complete mastery of the vocab
    - ⭐️⭐️⭐️⭐: Need 1 or 2 more exposures to reach complete mastery
    - ⭐️⭐️⭐️: Know the meaning but cannot effectively utilize it in conversations
    - ⭐️⭐️: Understand the connotation
    - ⭐️: Unclear

<br>  

<br>  

# Algorithm Development Procedure

### 1. Collect Vocabularies in [Notion database](https://andyhomepage.notion.site/Vocabularies-c97b642944854b44826d8a1ce73bc3da)

This process takes less than 10 seconds to record.
I would simply go into the Notion application and type in the vocabulary I wish to learn.

### 2. Connect to Slack API

Connecting to Slack API allows to set up timed notifications for the exposures of the vocabularies.

### 3. Connect to [Lingua Robot(RapidAPI) API](https://rapidapi.com/rokish/api/lingua-robot/details)

Although there exists a PyDictionary module that allows direct retrieval of vocabulary definitions, connecting to the Lingua Robot API provides a broader range of words and more informative descriptions. Also, it allows to generate vocab examples and synonyms that will help with overall comprehension of the each word.

### 4. Write Smart (Vocabulary) Suggesting Algorithm

These are some of the **conditions & procedures** when suggesting vocabularies:
- Sort the vocabularies with minimum counts(exposures) so that suggestions are not clustered
- Eliminate redundant or consecutive suggestions
- Prioritize the vocab catered to the user's needs ("High", "Medium", "Low")
    - When learning vocabularies, sometimes there exist words that need to be learned more urgently than others. This feature takes care of that. 
- Find **an appropriate number of vocabularies** to suggest
    - Depending on how many vocabs are on the waiting list, the number of suggestions will adjust accordingly
    - The reason for not having a fixed number of suggestions is to prevent the cloggage of too many vocabularies on the waitlist
- Suggest vocabularies a day divided into three sections: morning, afternoon, and night
- Add the number of exposure by one every time each vocabulary is exposed
- Update the above changes to the Notion Vocabulary database

<br>

<br>  

# User Experience

Since adding the vocabularies in the Notion database can be burdensome (especially using mobile devices), the users can **directly type in the slack message to add new words to their databases.** The algorithm will also supplement any missing information to function correctly. Also, with the simple manual, users can add images, prioritize their words, and add contexts to the vocabulary in simple steps. The following are some of the key features that amplify user experience.
- **Visual Learning**: automatically add images associated with the vocabulary (scraped from google images)
- **Auditory Learning**: provide Baroque music that is 3 ~ 5 minutes for the amplified learning experience.
    - Since Baroque music travels 50 to 80 beats per minute, it stabilizes our mental state ([For More](https://news.stanford.edu/news/2007/august8/med-music-080807.html))
- Type in vocabulary desired to learn in a Slack message, which will be automatically stored in the user's Notion database
    - Estimated time for storing a vocabulary through Slack is between 3 seconds to 15 seconds, depending on the user and the input information
- Modify the timing of the slack notifications according to the user's timezone
- Generate different manuals in Slack according to the user's primary language (Korean or English)
- Provide a direct link to the user's tailored Notion database for easier access

| | |
|:-------------------------:|:-------------------------:|
| **English Manual** | **Korean Manual** |
| <img align="center" src="https://github.com/AndyLeeProjects/vocab_learning_algorithm/blob/main/img_files/Slack_manual_en.jpg" width="400" height="350" > | <img align="center" src="https://github.com/AndyLeeProjects/vocab_learning_algorithm/blob/main/img_files/Slack_manual_kr.jpg" width="400" height="350" >

<br>  

<br>  

# Automation Video & Slack Notification

### Automation Sample

https://user-images.githubusercontent.com/84836749/174498756-449be7fd-045f-4c55-ab07-4f8227e26f6f.mp4

### Slack Notification Sample

https://user-images.githubusercontent.com/84836749/189543874-004b028d-3ca3-4d03-8175-696224e0609c.MP4
