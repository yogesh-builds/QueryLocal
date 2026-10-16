# Benchmark comparison

| Metric | gemini_gemini-3.5-flash-lite_50 | ollama_qwen2.5-coder_3b_50 |
|---|---|---|
| Correct | 44/50 (88.0%) | 35/50 (70.0%) |
| Average seconds per question | 9.7 | 10.9 |
| Median seconds per question | 6.5 | 8.3 |
| Ran but returned wrong rows | 6 | 12 |
| SQL error after retries | 0 | 3 |
| Asked to clarify or said impossible | 0 | 0 |

## Correct only for gemini_gemini-3.5-flash-lite_50

- **Give the code of the airport with the least flights.**
  - correct SQL: `SELECT T1.AirportCode FROM AIRPORTS AS T1 JOIN FLIGHTS AS T2 ON T1.AirportCode = T2.DestAirport OR T1.AirportCode = T2.SourceAirport GROUP BY T1.AirportCode ORDER BY count(*) LIMIT 1`
  - ollama_qwen2.5-coder_3b_50: `SELECT AirportCode FROM airports GROUP BY AirportCode ORDER BY COUNT(*) ASC LIMIT 1`
- **What are the ids and names of all countries that either have more than 3 car makers or produce fiat model ?**
  - correct SQL: `select t1.countryid , t1.countryname from countries as t1 join car_makers as t2 on t1.countryid = t2.country group by t1.countryid having count(*) > 3 union select t1.countryid , t1.countryname from countries as t1 join car_makers as t2 on t1.countryid = t2.country join model_list as t3 on t2.id = t3.maker where t3.model = 'fiat';`
  - ollama_qwen2.5-coder_3b_50: `SELECT T2.CountryId, T2.CountryName FROM car_makers AS T1 INNER JOIN countries AS T2 ON T1.Country = T2.CountryId WHERE T1.Maker = 'Fiat' OR (SELECT COUNT(*) FROM car_makers AS T3 WHERE T3.Country = T2.CountryId) > 3`
- **Find the major and age of students who do not have a cat pet.**
  - correct SQL: `SELECT major , age FROM student WHERE stuid NOT IN (SELECT T1.stuid FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid = T2.stuid JOIN pets AS T3 ON T3.petid = T2.petid WHERE T3.pettype = 'cat')`
  - ollama_qwen2.5-coder_3b_50: `SELECT T1.major, T1.age FROM Student AS T1 LEFT JOIN Has_Pet AS T2 ON T1.StuID = T2.StuID LEFT JOIN Pets AS T3 ON T2.PetID = T3.PetID WHERE T3.PetType != 'cat'`
- **List the names of all winners who played in both 2013 and 2016.**
  - correct SQL: `SELECT winner_name FROM matches WHERE YEAR = 2013 INTERSECT SELECT winner_name FROM matches WHERE YEAR = 2016`
  - ollama_qwen2.5-coder_3b_50: `SELECT DISTINCT T2.winner_name FROM rankings AS T1 INNER JOIN matches AS T2 ON T1.player_id = T2.winner_id WHERE T1.ranking_date LIKE '2013%' INTERSECT SELECT DISTINCT T2.winner_name FROM rankings AS T1 INNER JOIN matches AS T2 ON T1.player_id = T2.winner_id WHERE T1.ranking_date LIKE '2016%'`
- **Find the states where both owners and professionals live.**
  - correct SQL: `SELECT state FROM Owners INTERSECT SELECT state FROM Professionals`
  - ollama_qwen2.5-coder_3b_50: `no such column: T2.owner_id`
- **Which student has enrolled for the most times in any program? List the id, first name, middle name, last name, the number of enrollments and student id.**
  - correct SQL: `SELECT T1.student_id , T1.first_name , T1.middle_name , T1.last_name , count(*) , T1.student_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id = T2.student_id GROUP BY T1.student_id ORDER BY count(*) DESC LIMIT 1`
  - ollama_qwen2.5-coder_3b_50: `SELECT T1.student_id, T1.first_name, T1.middle_name, T1.last_name, COUNT(*) AS num_enrollments FROM Students AS T1 INNER JOIN Student_Enrolment AS T2 ON T1.student_id = T2.student_id GROUP BY T1.student_id ORDER BY num_enrollments DESC LIMIT 1`
- **Which owner has paid the largest amount of money in total for their dogs? Show the owner id and zip code.**
  - correct SQL: `SELECT T1.owner_id , T1.zip_code FROM Owners AS T1 JOIN Dogs AS T2 ON T1.owner_id = T2.owner_id JOIN Treatments AS T3 ON T2.dog_id = T3.dog_id GROUP BY T1.owner_id ORDER BY sum(T3.cost_of_treatment) DESC LIMIT 1`
  - ollama_qwen2.5-coder_3b_50: `no such column: T4.charge_id`
- **What model has the most different versions?**
  - correct SQL: `SELECT Model FROM CAR_NAMES GROUP BY Model ORDER BY count(*) DESC LIMIT 1;`
  - ollama_qwen2.5-coder_3b_50: `SELECT Model FROM model_list GROUP BY Model ORDER BY COUNT(*) DESC LIMIT 1`
- **What is the name of the winner with the most rank points who participated in the Australian Open tournament?**
  - correct SQL: `SELECT winner_name FROM matches WHERE tourney_name = 'Australian Open' ORDER BY winner_rank_points DESC LIMIT 1`
  - ollama_qwen2.5-coder_3b_50: `SELECT T2.winner_name FROM rankings AS T1 INNER JOIN matches AS T2 ON T1.player_id = T2.winner_id WHERE T2.tourney_name = 'Australian Open' GROUP BY T2.winner_name ORDER BY T1.ranking_points DESC LIMIT 1`
- **What is the name and directors of all the cartoons that are ordered by air date?**
  - correct SQL: `SELECT title , Directed_by FROM Cartoon ORDER BY Original_air_date`
  - ollama_qwen2.5-coder_3b_50: `no such column: T2.Title`

## Correct only for ollama_qwen2.5-coder_3b_50

- **How many countries have a republic as their form of government?**
  - correct SQL: `SELECT count(*) FROM country WHERE GovernmentForm = "Republic"`
  - gemini_gemini-3.5-flash-lite_50: `SELECT COUNT(*) FROM country WHERE GovernmentForm LIKE '%Republic%'`

## Wrong for both models (5)

- Find the first name and age of students who have a dog but do not have a cat as a pet.
- What are the country codes for countries that do not speak English?
- Which African countries have a smaller population than that of any country in Asia?
- How many countries has more than 2 car makers ?
- What is name of the country that speaks the largest number of languages?
