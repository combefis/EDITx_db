from py2neo import Graph, Node, Relationship, NodeMatcher
import json
from flask import Flask

app = Flask(__name__)

# connection to te neo4j database
uri = "bolt://localhost:7687"
graph = Graph(uri, user="neo4j", password="editx")

#  Node matcher initialization
matcher = NodeMatcher(graph)


class Database:

    @staticmethod
    def add_field(field, level):

        """adds a field to the database

            :param field: the name of the field
            :param level: the relationship level of the field"""

        field_node = Node('Field', name=field, level=level)  # id?
        graph.create(field_node)

    @staticmethod
    def add_question(title, url):

        """adds a question to the database

            :param title: the title of the question
            :param url: the url that redirects to the question located on EDITx site"""

        question_node = Node('Question', title=title, url=url)
        graph.create(question_node)

    @staticmethod
    def add_buzz_word(name):

        """add a field to the database

            :param name: the name of the buzz word"""

        buzz_word = Node('BuzzWord', name=name)
        graph.create(buzz_word)

    @staticmethod
    def add_subfield_relationship(field, subfield):

        """adds a relationship between a field and its subfield to the database

            :param field: the name of the field
            :param subfield: the name of the subfield"""

        #if (fieldLevel < subfieldLevel):
        f1 = matcher.match("Field", name=field).first()
        f2 = matcher.match("Field", name=subfield).first()
        graph.merge(Relationship(f1, 'include', f2))
        #else:
        #    print("the level of the first param must be smaller than the level of the second")

    @staticmethod
    def add_is_linked_to_relationship(buzzword, field):

        """adds a relationship between a field and its subfield to the database

            :param buzzword: the name of the buzz word
            :param field: the name of the field linked to the buzz word"""

        #if(field1Level > field2Level):
        f1 = matcher.match("BuzzWord", name=buzzword).first()
        f2 = matcher.match("Field", name=field).first()
        graph.merge(Relationship(f1, 'is_linked_to', f2))
        #else:
        #    print("the level of the first param must be greater than the level of the second")

    @staticmethod
    def add_concerns_relationship(field1, field2):

        """add a relationship between a field and its subfield to the database

            :param field1: the name of the field
            :param field2: the name of the field linked to the field1"""

        # if(field1Level > field2Level):
        f1 = matcher.match("Field", name=field1).first()
        f2 = matcher.match("Field", name=field2).first()
        graph.merge(Relationship(f1, 'concerns', f2))
        # else:
        #    print("the level of the first param must be greater than the level of the second")

    @staticmethod
    def add_question_relationship(subfield, question_title):

        """adds a relationship between a field and its subfield to the database

            :param subfield: the name of the field
            :param question_title: the title of the question linked to the subfield"""

        f = matcher.match("Field", name=subfield).first()
        q = matcher.match("Question", title=question_title).first()
        graph.merge(Relationship(f, 'question', q))


    @staticmethod
    def find_one_field(name):

        """finds a field in the database by its name

            :param name: the name of the field
            :returns: the field searched as a node object"""

        field_node = matcher.match("Field", name=name).first()
        return field_node

    @staticmethod
    def find_one_buzzword(name):

        """finds a buzz word in the database by its name

            :param name: the name of the buzz word
            :returns: the buzz word searched as a node object"""

        buzzword_node = matcher.match("BuzzWord", name=name).first()
        return buzzword_node

    '''for questions and subfiels of a field'''     #attention juste pour un niveau, autre fonction pour trouver pour afficher tout le sous-graphe
    @staticmethod
    def find_sub_nodes(field_name, relationName):

        """finds the subnodes of a field with the desired relationship

            :param field_name: the name of the field
            :param relationName: the name of the desired relationship
            :returns: a list of all subnodes of the field concerned by the relationship wished"""

        f = Database.find_one_field(field_name)
        node_list = []
        for rel in graph.match((f,), r_type=relationName):
            node_list.append(rel.end_node)   # type of "rel.end_node" : Node
        return node_list

    @staticmethod
    def find_same_level_fields(level):

        """finds all fields that have the same level in the classification

            :param level: the desired level
            :returns: a list of all fields that have the desired level"""

        fields_nodes = matcher.match("Field", level=level)
        nodes_list = []
        for field in fields_nodes:
            nodes_list.append(field)
        return nodes_list

    @staticmethod
    def find_buzz_words():

        """finds all buzz words

            :returns:  a dictionary with as key 'names' and as value a list with all buzz words"""

        fields = graph.run('''MATCH (f:BuzzWord)
                              WITH f
                              ORDER BY f.name
                              RETURN collect(f.name) AS names''').data()
        return fields

    @staticmethod
    def find_buzz_word_fields(buzzword):

        """finds the fields (and the fields that include them ) linked to the desired buzz word

            :param buzzword: the desired level
            :returns: a list of dictionaries that represent the fields (and the fields that include them ) linked to
                        the desired buzz word
                      --> list of dictionaries whose key values are dictionaries whose key values are lists"""

        lev3 = graph.run('''MATCH (b: BuzzWord{name:{name}})-[:is_linked_to]->(f3: Field{level:3})<-[:include]-(f2: Field)
                               OPTIONAL MATCH (f2)<-[:include]-(f1:Field) 
                               WITH f2, f3, f1
                               ORDER BY f2.name
                               RETURN f2.name AS name, collect(f3.name) AS subfields, f1.name AS name_lev1
                               ORDER BY f1.name''', name=buzzword).data()

        lev1 = graph.run('''MATCH (b: BuzzWord{name:{name}})-[:is_linked_to]->(f1: Field{level:1})
                            RETURN f1.name AS name_lev1
                            ORDER BY f1.name''', name=buzzword).data()

        lev2 = graph.run('''MATCH (b: BuzzWord{name:{name}})-[:is_linked_to]->(f2: Field{level:2})<-[:include]-(f1: Field)
                            WITH f2, f1
                            ORDER BY f2.name
                            RETURN f2.name AS name, f1.name AS name_lev1
                            ORDER BY f1.name''', name=buzzword).data()

        # Construction of a list of dictionaries whose key values are dictionaries whose key values are lists
        final_list = []

        for field in lev1:
            final_dict = {}
            level1 = field['name_lev1']
            del field['name_lev1']
            final_dict['name'] = level1
            final_dict['subfields'] = {}
            final_list.append(final_dict)

        for field in lev2:
            final_dict = {}
            level1 = field['name_lev1']
            del field['name_lev1']
            final_dict['name'] = level1
            field['subfields'] = []
            final_dict['subfields'] = field
            final_list.append(final_dict)

        for field in lev3:
            final_dict = {}
            level1 = field['name_lev1']
            del field['name_lev1']
            final_dict['name'] = level1
            final_dict['subfields'] = field  # ex: 'subfields': {'name': 'process management','subfields': ['threads']}}
            final_list.append(final_dict)

        # order alphabetically the level 1
        sorted_final_list = sorted(final_list, key=lambda k: k['name'])

        return sorted_final_list

    @staticmethod
    def delete_field(field_name):

        """Deletes the field and all its relationships

            :param field_name: the name of the field to delete"""

        field_node = Database.find_one_field(field_name)
        graph.delete(field_node)

    @staticmethod
    def delete_buzz_word(buzzword):

        """Deletes the buzz word and all its relationships

            :param buzzword: the name of the buzz word to delete"""

        field_node = Database.find_one_buzzword(buzzword)
        graph.delete(field_node)

    @staticmethod
    def delete_question(question_title):

        """Deletes the question and all its relationships

            :param question_title: the title of the question to delete"""

        question_node = matcher.match("Question", title=question_title).first()
        graph.delete(question_node)

    @staticmethod
    def delete_relation(field1, field2, relation_name):

        """Deletes the relationship between 2 fields

            :param field1: the name of one of the two fields
            :param field2: the name of the other field
            :param relation_name: the relationship between the two fields"""

        start_node = Database.find_one_field(field1)
        end_node = Database.find_one_field(field2)
        #  be careful to check the existence of the nodes before
        relationship = graph.match_one(nodes=(start_node, end_node), r_type=relation_name)
        graph.separate(relationship)

    @staticmethod
    def edit_field(field_name, new_name, new_level):

        """Edits the properties of a field

            :param field_name: the name of the field to edit
            :param new_name: the new name of the field
            :param new_level: the new level of the field"""

        field_node=Database.find_one_field(field_name)

        field_node['name'] = new_name
        field_node['level'] = new_level

        graph.push(field_node)

    @staticmethod
    def edit_question(title, new_title, new_url):

        """Edits the properties of a question

            :param title: the name of the question to edit
            :param new_title: the new title of the question
            :param new_url: the new url of the question"""

        question_node = matcher.match("Question", title=title).first()

        question_node['title'] = new_title
        question_node['url'] = new_url

        graph.push(question_node)

    @staticmethod
    def find_questions(field_name):

        """finds all questions linked to a field

            :param field_name: the name of the field
            :returns: a list of dictionaries that represent all questions linked to the field"""

        questions = graph.run('''MATCH (f:Field{name: {name}})-[:include*0..2]->(f2:Field)-[:question]->(q:Question)
                                 RETURN q.title AS title, q.url AS url 
                                 ORDER BY q.title''', name=field_name).data()

        return questions


    @staticmethod
    def find_subfields(field_name):

        """finds all subfields of a field

            :param field_name: the name of the field
            :returns: a list of dictionaries that represent all subfields of the field"""

        fields = graph.run('''MATCH (f:Field{name:{name}})-[:include]->(f2:Field) 
                              OPTIONAL MATCH (f)-[:include]->(f2)-[:include]->(f3:Field)
                              WITH f2, f3
                              ORDER BY f3.name
                              RETURN f2.name AS name, collect(f3.name) AS subfields
                              ORDER BY f2.name''', name=field_name).data()  # empty list if level 3

        return fields

    @staticmethod
    def find_concerned_fields(field_name):

        """finds all fields linked to a field

            :param field_name: the name of the field
            :returns: the names of the fields linked to the desired field"""

        fields = graph.run('''OPTIONAL MATCH (f:Field{name:{name}})-[:concerns]-(f2:Field) 
                              RETURN f2.name AS name
                              ORDER BY f2.name''', name=field_name).data()

        return fields

    @staticmethod
    def find_all_fields():

        """finds all fields of the classification

            :returns: all fields of the classification"""

        levels_1_2 = graph.run('''MATCH (f:Field{level:1})-[:include]->(f2:Field) 
                                  WITH f, f2
                                  ORDER BY f2.name
                                  RETURN f.name AS name, collect(f2.name) AS subfields
                                  ORDER BY f.name''').data()

        levels_2_3 = graph.run('''MATCH (f:Field{level:1})-[:include]->(f2:Field)-[:include]->(f3:Field)
                                  WITH f2, f3
                                  ORDER BY f3.name
                                  RETURN f2.name AS name_L2, collect(f3.name) AS subfields_L3
                                  ORDER BY f2.name''').data()

        all_fields = []
        for rootField in levels_1_2:
            root_field_dict = {}
            root_field_dict["name"] = rootField['name']
            root_field_dict["subfields"] = []
            fields_used = []

            for field_L2 in levels_2_3:
                if field_L2["name_L2"] in rootField['subfields']:  # rootField['subfields'] is an str list
                    sub_field_dict = {}
                    sub_field_dict["name"] = field_L2['name_L2']
                    sub_field_dict["subfields"] = []
                    for field_L3 in field_L2['subfields_L3']:
                        if field_L3 not in sub_field_dict["subfields"]:   # to not have 2 x subfields
                           sub_field_dict["subfields"].append(field_L3)   # when one node included by two fields
                    root_field_dict["subfields"].append(sub_field_dict)
                    fields_used.append(field_L2['name_L2'])

            for field_L2_name in rootField['subfields']:  # for levels 2 which don't have a level 3
                if field_L2_name not in fields_used:
                    sub_field_dict = {}
                    sub_field_dict["name"] = field_L2_name
                    sub_field_dict["subfields"] = []
                    root_field_dict["subfields"].append(sub_field_dict)

            all_fields.append(root_field_dict)

        # sorts alphabetically
        for x in all_fields:
            sorted_list_of_dict = sorted(x["subfields"], key=lambda k: k['name'])   # sort a list of dictionaries by the
                                                                                    # key: name (level 2)
            x["subfields"] = sorted_list_of_dict
            '''for y in x["subfields"]:
                sortedList = sorted(y["subfields"])  #sort simply a list of strings (level 3)
                y["subfields"] = sortedList'''

        return all_fields

    @staticmethod
    def delete_all():

        """Clears the entire database"""

        graph.run('''MATCH (n)
                     DETACH DELETE n ''')

    @staticmethod
    def fields_creation():

        """Creates the classification into the database"""

        with app.open_resource('db_creation/classification.json') as file:
            fields = json.load(file)['items']

            for field in fields:
                Database.add_field(field['field'], 1)
                for subfield in field['subfields']:
                    Database.add_field(subfield['subfield'], 2)
                    Database.add_subfield_relationship(field['field'], subfield['subfield'])
                    for subsubfield in subfield['subsubfields']:
                        Database.add_field(subsubfield, 3)
                        Database.add_subfield_relationship(subfield['subfield'], subsubfield)

            # because one node is linked to more of one other node
            Database.add_subfield_relationship('services', 'cloud computing')
            Database.add_subfield_relationship('Software', 'DBMS')
            Database.add_subfield_relationship('Computer systems', 'Operating systems') # car os a plsr champs, comment faire dans arborescence?
            Database.add_subfield_relationship('mobile development', 'Visual Studio')
            Database.add_subfield_relationship('mobile development', 'Unity')
            Database.add_subfield_relationship('Software', 'os types')

    @staticmethod
    def buzz_words_links_creation():

        """Creates buzz words and theirs relationship with the classification into the database"""

        with app.open_resource('db_creation/buzz_words_links.json') as file:
            data = json.load(file)

            for key, value in data.items():
                Database.add_buzz_word(key)
                for field in value:
                    Database.add_is_linked_to_relationship(key, field)

    @staticmethod
    def fields_links_creation():

        """Creates the relationship between fields that are linked to each other"""

        with app.open_resource('db_creation/fields_links.json') as file:
            data = json.load(file)

            for key, value in data.items():
                for field in value:
                    Database.add_concerns_relationship(key, field)

    @staticmethod
    def database_creation():

        """Create the entire Editx Database"""

        Database.fields_creation()
        Database.buzz_words_links_creation()
        Database.fields_links_creation()
