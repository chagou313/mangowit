import json

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse


TOPICS = {
    "physiology_knowledge": ("physiology", "生理知识图谱"),
    "psychology_knowledge": ("psychology", "心理知识图谱"),
    "safety_knowledge": ("safety", "安全知识图谱"),
}


def load_graph(topic):
    path = settings.BASE_DIR / "static" / "kg" / f"{topic}.json"
    return json.loads(path.read_text(encoding="utf-8"))


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class KnowledgeGraphPageTests(TestCase):
    def test_each_graph_page_loads_its_own_data(self):
        for url_name, (topic, heading) in TOPICS.items():
            path = reverse(url_name)
            with self.subTest(page=path):
                response = self.client.get(path)
                self.assertContains(response, f"<h1>{heading}</h1>", html=True)
                self.assertContains(response, f'data-src="/static/kg/{topic}.json"')
                self.assertContains(response, "/static/kg/knowledge-graph.js")
                self.assertNotContains(response, "bootstrap")


class KnowledgeGraphDataTests(TestCase):
    def test_graph_data_is_consistent(self):
        for topic, _ in TOPICS.values():
            with self.subTest(topic=topic):
                graph = load_graph(topic)
                ids = [n["id"] for n in graph["nodes"]]
                self.assertEqual(len(ids), len(set(ids)))
                for node in graph["nodes"]:
                    self.assertEqual(node["label"], node["label"].strip())
                    self.assertIn(node["group"], {"female", "male"})
                    self.assertTrue(node["type"])
                edge_keys = [(e["from"], e["to"], e["label"]) for e in graph["edges"]]
                self.assertEqual(len(edge_keys), len(set(edge_keys)), "duplicate edges")
                for source, target, _ in edge_keys:
                    self.assertIn(source, ids)
                    self.assertIn(target, ids)
