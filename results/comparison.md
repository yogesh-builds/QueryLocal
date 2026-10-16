# Benchmark comparison

| Metric | ollama_qwen2.5-coder_3b_50 | ollama_qwen2.5-coder_3b-rows3_50 |
|---|---|---|
| Correct | 35/50 (70.0%) | 35/50 (70.0%) |
| Average seconds per question | 10.9 | 16.5 |
| Median seconds per question | 8.3 | 7.7 |
| Ran but returned wrong rows | 12 | 11 |
| SQL error after retries | 3 | 4 |
| Asked to clarify or said impossible | 0 | 0 |

## Correct only for ollama_qwen2.5-coder_3b_50

- **What are all the song names by singers who are older than average?**
  - correct SQL: `SELECT song_name FROM singer WHERE age > (SELECT avg(age) FROM singer)`
  - ollama_qwen2.5-coder_3b-rows3_50: `no such column: T2.Song_Name`

## Correct only for ollama_qwen2.5-coder_3b-rows3_50

- **What is the name of the winner with the most rank points who participated in the Australian Open tournament?**
  - correct SQL: `SELECT winner_name FROM matches WHERE tourney_name = 'Australian Open' ORDER BY winner_rank_points DESC LIMIT 1`
  - ollama_qwen2.5-coder_3b_50: `SELECT T2.winner_name FROM rankings AS T1 INNER JOIN matches AS T2 ON T1.player_id = T2.winner_id WHERE T2.tourney_name = 'Australian Open' GROUP BY T2.winner_name ORDER BY T1.ranking_points DESC LIMIT 1`

## Wrong for both models (14)

- Give the code of the airport with the least flights.
- What are the ids and names of all countries that either have more than 3 car makers or produce fiat model ?
- Find the first name and age of students who have a dog but do not have a cat as a pet.
- Find the major and age of students who do not have a cat pet.
- List the names of all winners who played in both 2013 and 2016.
- Find the states where both owners and professionals live.
- What are the country codes for countries that do not speak English?
- Which student has enrolled for the most times in any program? List the id, first name, middle name, last name, the number of enrollments and student id.
- Which owner has paid the largest amount of money in total for their dogs? Show the owner id and zip code.
- Which African countries have a smaller population than that of any country in Asia?
- How many countries has more than 2 car makers ?
- What is name of the country that speaks the largest number of languages?
- What model has the most different versions?
- What is the name and directors of all the cartoons that are ordered by air date?
