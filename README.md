# Employee_Recommendation_Knowledge_Graph
Building Knowledge Graph
At this phase of the project, building a knowledge graph with all the available attributes together is impossible. So, we build a separate knowledge graph for attributes like university, skill and education etc. to understand the graph. It turns out very well, as we can clearly visualize both entities and the relationship (which is basically the attribute name in this case).
1. Knowledge Graph of “University”
To build the first knowledge graph, which is by taking the first attribute ‘University’, the raw data has the universities he/she has attended and the ranking of those universities. The result was to retain only the top-ranking universities out of all those universities. Luckily, the universities were already arranged in higher to lower ranking order and all we had to do is to extract the first of those universities. The only challenging part was to work with python nested dictionary. 

2. Knowledge Graph of “Degree Level”
The next task is to build knowledge graph using ‘Degree level’. In this case most of the datapoints are categorized into three types viz. diploma, bachelor’s and master's but the challenging part was there are various versions of the same degrees as bachelor has been mentioned as bachelors in, bachelors of, bachelors etc, and similarly for masters and diploma. So, in order to standardized them we created a function which matches the first three letters of each datapoint and if, it is 'bac' then we convert the entire string to bachelors, if 'mas' then masters and if 'dip' then diploma and None in all other cases. In this way we can group all the candidates under three sections and build a knowledge graph according to that.

3. Knowledge Graph of “Degree Type”
In order to extract the Degree Specialization/ Degree Type, we first cleaned the data using regex library to perform operations like remove newline character, special characters, slashes etc. making sure we have only letters and number in the string, and everything is in lowercase. Once the data is cleaned, we tokenize all the strings using spaCy library. The next step was to create a generic rule to set the index for extraction. After extracting the tokens at specific indexes, there are still few tokens, which are not meaningful and keeping it in mind each token represents a node we cannot go with any non-meaningful token and it is required to standardize the degree type; an exhaustive python list was created which contains all the potential degree types, which later was compared with each extracted token and finally build the graph. The following graph shows the details of the candidate and their specialization of course.

4. Knowledge Graph of “Skills”
The next task is to build the knowledge graph from “skills”. We started the process by comparing each skill with all the items from an exhaustive list and retain all the matches. Now we have filtered skill set for each candidate. At this point the most challenging part was to arrange the data frame in such a way that every skill can be treated as a single node. For example, if a candidate is skilled in python, java, scala and html, we cannot treat this as a single string so used a function called ‘explode’ from pandas data frame which takes each item of the list and separate them in individual rows, keeping the same index. We require to do this operation as when we pass the data frame to graph, we want separate node for each skill and finally build the knowledge graph.

5. Combined Knowledge Graph
Once we get a clear picture of the graph which is built separately our next step is to combine the knowledge graph to build a complete graph for the whole dataset. To build the graph, we used the library called ‘networkx’. The biggest challenge to combine the graphs was that we can combine only two graphs at a time. To construct the final graph, first we combine graphs of skills and university and then combine degree type and degree level and finally combine the two combined graphs.