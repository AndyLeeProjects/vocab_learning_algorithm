# Vocabulary Analysis

When I was younger, a Psychology Professor came up to me and said something that I remember to this day. 
He said, "To bring the information from the unconscious level to the level of consciousness, it takes, on average, seven exposures."
Although it is super random, and not sure why I remember this, it is true that the professor has said this to me.
Recently, I have been trying to develop a system that would allow me to "memorize" vocabulary more efficiently. 
This was because compared to all the new vocabularies that I learned every day, the ones that I actually absorbed were only a handful. 
Thus, I decided to test the hypothesis of the Psychology Professor. 


<br>  
<br>  

## Procedure
The code was relatively simple, but the procedure needed a little thought.
<br>  
### 1. Collect Vocabularies in Notion database
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
