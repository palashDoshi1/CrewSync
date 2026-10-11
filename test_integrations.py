"""Protocol checks use mock services; they do not claim live provider verification."""
import json
import unittest
from datetime import date
from unittest.mock import patch, MagicMock
import httpx
from openai import OpenAI
from ai_client import create_event, draft_messages
from product import demo_proposal, new_plan
from storage import EventStore
from coordinator import parse_csv,VOLUNTEERS,SHIFTS

class IntegrationContracts(unittest.TestCase):
    def test_ai_plan_uses_configured_url_model_and_validated_json(self):
        volunteers=parse_csv(VOLUNTEERS,'volunteers')
        def handler(request):
            self.assertEqual(str(request.url),'https://example.test/custom/v1/chat/completions')
            payload=json.loads(request.content)
            self.assertEqual(payload['model'],'sponsor-model')
            content=json.loads(payload['messages'][1]['content'])
            self.assertEqual(content['request'],'A campus giving event')
            return httpx.Response(200,json={'id':'mock','object':'chat.completion','created':0,'model':'sponsor-model','choices':[{'index':0,'message':{'role':'assistant','content':json.dumps(demo_proposal(date(2026,10,11)))},'finish_reason':'stop'}]})
        real=OpenAI
        with patch('openai.OpenAI',side_effect=lambda **kw:real(**kw,http_client=httpx.Client(transport=httpx.MockTransport(handler)))):
            result=create_event('test-key','https://example.test/custom/v1','sponsor-model','A campus giving event',volunteers,date(2026,10,11))
        self.assertEqual(len(result['shifts']),3)
    def test_missing_configuration_and_http_rejected(self):
        for url in ['', 'http://example.test/v1']:
            with self.assertRaises(ValueError):draft_messages('test-key',url,'model',{})
    def test_mongodb_atomic_snapshot_and_retrieval_contract(self):
        client=MagicMock();collection=MagicMock()
        client.__getitem__.return_value.__getitem__.return_value=collection
        p=new_plan('Demo','2026-10-11','HUB',parse_csv(VOLUNTEERS,'volunteers'),parse_csv(SHIFTS,'shifts'))
        p['api_key']='must-not-persist'
        with patch('pymongo.MongoClient',return_value=client):
            store=EventStore(uri='mongodb+srv://example.test',database='crewsync')
            store.save(p)
            args,kw=collection.replace_one.call_args
            self.assertEqual(args[0],{'_id':p['id']})
            self.assertTrue(kw['upsert'])
            self.assertNotIn('api_key',args[1])
            saved=dict(args[1]);saved.pop('_id')
            collection.find.return_value.sort.return_value.limit.return_value=[saved]
            self.assertEqual(store.list()[0]['assignments'],p['assignments'])
        self.assertEqual(client.close.call_count,2)
