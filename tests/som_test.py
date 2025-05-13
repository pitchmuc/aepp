#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

from aepp.som import Som
import unittest
from unittest.mock import patch, MagicMock


class SomTest(unittest.TestCase):

    def test_som_instantiation_empty(self):
        mysom = Som()
        assert bool(mysom.get()) == False

    def test_som_instantiation_notEmpty(self):
        mysom = Som({'data':'key'})
        assert bool(mysom.get()) == True

    def test_som_assignments_simple(self):
        mysom = Som()
        mysom.assign('string','1')
        assert type(mysom.get('string')) == str
        assert mysom.get('string') == '1'
        mysom.assign('integer',1)
        assert mysom.get('integer') == 1
        mysom.assign('mylist',[0])
        assert type(mysom.get('mylist')) == list
        mysom.assign('a.b','test')
        assert mysom.get('a.b') == 'test'
        mysom.assign('myset',set([1,2]))
        assert type(mysom.get('myset')) == set
        mysom.assign('mytuple',(1,2))
        assert type(mysom.get('mytuple')) == tuple
        mysom.assign('my.fallback',None,'fallback')
        assert mysom.get('my.fallback') == 'fallback'
        assert mysom.get('my.fallbacks',False) == False ## testing Falsy fallback
    
    def test_som_assignments_list(self):
        mysom = Som()
        mysom.assign('mylist',[0])
        mysom.assign('mylist',1)
        assert type(mysom.get('mylist')) == list
        assert len(mysom.get('mylist')) == 2
        mysom.assign('mylist2',2,params={"type":list})
        assert type(mysom.get('mylist2')) == list
        mysom.assign('data.mylist.[0]',1)
        assert type(mysom.get('data.mylist')) == list
        assert len(mysom.get('data.mylist')) == 1
        assert mysom.get('data.mylist.1') == True
        mysom.assign('data.mylist.[1]',1)
        assert len(mysom.get('data.mylist')) == 2
        mysom.assign('data.mylist.[1]',3)
        assert len(mysom.get('data.mylist')) == 2
        assert mysom.get('data.mylist.1') == 3
        mysom.assign('data.mylist',[1,2])
        assert len(mysom.get('data.mylist')) == 3
        assert type(mysom.get('data.mylist.2')) == list
        mysom.assign('data.mylist',(1,2))
        assert len(mysom.get('data.mylist')) == 4
        assert type(mysom.get('data.mylist.3')) == tuple
        mysom.assign('data.mylist',set([1,2]))
        assert len(mysom.get('data.mylist')) == 5
        assert type(mysom.get('data.mylist.4')) == set

    def test_som_assignments_set(self):
        mysom = Som()
        mysom.assign('myset',set([0]))
        mysom.assign('myset',1)
        assert type(mysom.get('myset')) == set
        assert len(mysom.get('myset')) == 2
        mysom.assign('myset2',2,params={"type":set})
        assert type(mysom.get('myset2')) == set
        assert mysom.get('myset2.2') == True
        mysom.assign('myset',[2,3])
        assert type(mysom.get('myset')) == set
        assert mysom.get('myset.2') == True
        mysom.assign('myset',(3,4))
        assert type(mysom.get('myset')) == set
        assert mysom.get('myset.4') == True
        mysom.assign('myset',set([4,5]))
        assert type(mysom.get('myset')) == set
        assert mysom.get('myset.5') == True
    
    def test_som_assignments_tuple(self):
        mysom = Som()
        mysom.assign('mytuple',tuple([0]))
        mysom.assign('mytuple',1)
        assert type(mysom.get('mytuple')) == tuple
        assert len(mysom.get('mytuple')) == 1
        mysom.assign('mytuple2',2,params={"type":tuple})
        assert type(mysom.get('mytuple2')) == tuple
        assert mysom.get('mytuple2.2') == True

    def test_som_complex_assignment_get(self):
        mysom = Som()
        mysom.assign('my.deep.value','foo')
        assert mysom.get('my.deep.value') == 'foo'
        assert mysom.get('my.deep.values','nothing') == 'nothing'
        assert mysom.get('my.deep.vvalues') is None
        mysom.assign('my.deep.list',1,params={"type":list})
        assert type(mysom.get('my.deep.list')) == list
        assert len(mysom.get('my.deep.list')) == 1
        mysom.assign('my.deep.list',2)
        assert len(mysom.get('my.deep.list')) == 2
        mysom.assign('my.deep.list',3,params={"override":True})
        assert type(mysom.get('my.deep.list')) == int
        mysom.assign('my.deep.list',1,params={"type":list})
        assert type(mysom.get('my.deep.list')) == list
        mysom.assign('my.deep.list',2,params={"type":set})
        assert type(mysom.get('my.deep.list')) == set
        assert len(mysom.get('my.deep.list')) == 2
        mysom.assign('my.deep.list',3,params={"type":tuple})
        assert type(mysom.get('my.deep.list')) == tuple
        assert len(mysom.get('my.deep.list')) == 3
        mysom.assign('my.deep.list',4)
        assert type(mysom.get('my.deep.list')) == tuple
        assert mysom.get('my.deep.list.0') == 4

    def test_som_merge(self):
        mysom = Som({"data":{'path1':'value1','list1':['value1'],'set1':set(['value1']),'tuple1':tuple(['value1'])}})
        assert mysom.get('data.path1') == 'value1'
        data2 = {
                'path1':'value2',
                'path2':'value2',
                'list1':['value2'],
                'list2':['value2'],
                'set1':set(['value2']),
                'set2':set(['value2']),
                'tuple1':tuple(['value2']),
                'tuple2':tuple(['value2'])
        }
        mysom.merge('data',data2)
        assert mysom.get('data.path1') == 'value2'
        assert mysom.get('data.path2') == 'value2'
        assert type(mysom.get('data.list1')) == list
        assert len(mysom.get('data.list1')) == 2
        assert len(mysom.get('data.list2')) == 1
        assert type(mysom.get('data.set1')) == set
        assert len(mysom.get('data.set1')) == 2
        assert len(mysom.get('data.set2')) == 1
        assert type(mysom.get('data.tuple1')) == tuple
        assert len(mysom.get('data.tuple1')) == 2
        assert len(mysom.get('data.tuple2')) == 1
        mysom.merge('data.list1',[1])
        mysom.merge('data.tuple1',tuple([1]))
        mysom.merge('data.set1',set([1]))
        assert len(mysom.get('data.list1')) == 3
        assert len(mysom.get('data.tuple1')) == 3
        assert len(mysom.get('data.set1')) == 3

    def test_som_merge_to_list(self):
        mysom = Som({"data":{'path1':'value1','set1':set(['value1']),'tuple1':tuple(['value1'])}})
        assert mysom.get('data.path1') == 'value1'
        data2 = {
                'path1':['value2'],
                'set1':['value2'],
                'tuple1':['value2'],
        }
        mysom.merge('data',data2)
        assert type(mysom.get('data.path1')) == list
        assert len(mysom.get('data.path1')) == 2
        assert type(mysom.get('data.set1')) == list
        assert len(mysom.get('data.set1')) == 2
        assert type(mysom.get('data.tuple1')) == list
        assert len(mysom.get('data.tuple1')) == 2
    
    def test_som_merge_to_set(self):
        mysom = Som({"data":{'path1':'value1','list1':['value1'],'tuple1':tuple(['value1'])}})
        assert mysom.get('data.path1') == 'value1'
        data2 = {
                'path1':set(['value2']),
                'list1':set(['value2']),
                'tuple1':set(['value2']),
        }
        mysom.merge('data',data2)
        assert type(mysom.get('data.path1')) == set
        assert len(mysom.get('data.path1')) == 2
        assert type(mysom.get('data.list1')) == set
        assert len(mysom.get('data.list1')) == 2
        assert type(mysom.get('data.tuple1')) == set
        assert len(mysom.get('data.tuple1')) == 2

    def test_som_merge_to_tuple(self):
        mysom = Som({"data":{'path1':'value1','list1':['value1'],'set1':set(['value1'])}})
        assert mysom.get('data.path1') == 'value1'
        data2 = {
                'path1':tuple(['value2']),
                'list1':tuple(['value2']),
                'set1':tuple(['value2']),
        }
        mysom.merge('data',data2)
        assert type(mysom.get('data.path1')) == tuple
        assert len(mysom.get('data.path1')) == 2
        assert type(mysom.get('data.list1')) == tuple
        assert len(mysom.get('data.list1')) == 2
        assert type(mysom.get('data.set1')) == tuple
        assert len(mysom.get('data.set1')) == 2

    def test_som_remove(self):
        mysom = Som({"data":{'path1':'value1','list1':['value1','value2','value3'],'set1':set(['value1','value2','value3']),'tuple1':tuple(['value1','value2','value3'])}})
        assert mysom.get('data.path1') == 'value1'
        mysom.remove('data.path1')
        assert mysom.get('data.path1') is None
        mysom.remove('data.list1.value2')
        assert len(mysom.get('data.list1')) == 2
        mysom.remove('data.list1.[0]')
        assert len(mysom.get('data.list1')) == 1
        mysom.remove('data.list1')
        assert mysom.get('data.list1') is None
        mysom.remove('data.set1.value1')
        assert len(mysom.get('data.set1')) == 2
        mysom.remove('data.set1')
        assert mysom.get('data.set1') is None
        mysom.remove('data.tuple1')
        assert mysom.get('data.tuple1') is None

    def test_clear(self):
        mysom = Som({"data":{'path1':'value1','list1':['value1','value2','value3'],'set1':set(['value1','value2','value3']),'tuple1':tuple(['value1','value2','value3'])}})
        assert mysom.get('data.path1') == 'value1'
        mysom.clear()
        assert mysom.get('data.path1') is None
        assert mysom.get('data.list1') is None
        assert mysom.get('data.set1') is None
        assert mysom.get('data.tuple1') is None

    def test_dataframe(self):
        data = {"data":
            {
                "myfield":"value",
                "myList" : [1,2,3],
                "arrayObject1":[
                {
                    "field_name":"array_item1",
                    "arrayObject2":[
                    {
                        "field_name":"array_item_1_1"
                    },
                    {
                        "field_name":"array_item_1_2"
                    }
                    ]
                },
                {
                    "field_name":"array_item2"
                }
                ]
            }
            }
        mySom = Som(data)
        df_flatten = mySom.to_dataframe()
        df_expands = mySom.to_dataframe(expand_arrays=True)
        assert len(df_flatten) == 1
        assert len(df_expands) == 3
        list_cols_flatten = ['data.myfield',
                            'data.myList',
                            'data.arrayObject1.[0].field_name',
                            'data.arrayObject1.[0].arrayObject2.[0].field_name',
                            'data.arrayObject1.[0].arrayObject2.[1].field_name',
                            'data.arrayObject1.[1].field_name']
        assert all(list_cols_flatten == df_flatten.columns)
        list_cols_expands = ['data.myfield',
                            'data.myList',
                            'data.arrayObject1',
                            'data.arrayObject1.field_name',
                            'data.arrayObject1.arrayObject2',
                            'data.arrayObject1.arrayObject2.field_name']
        assert all(list_cols_expands == df_expands.columns)
        





        





        
