# insert_sample_data.py

import os
import django

# 设置DJANGO_SETTINGS_MODULE环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mangowit.settings')

django.setup()

from AI_communication.models import AIQuestion, AIAnswer
from django.utils import timezone


def insert_data():
    questions_and_answers = [
        {
            "question": "什么是性教育?",
            "answer": "性教育是指对人类性行为、性健康、性关系等方面的知识、态度和技能的教育。"
        },
        {
            "question": "性教育的重要性是什么?",
            "answer": "性教育的重要性在于帮助人们了解性知识，预防性病和意外怀孕，建立健康的性观念和关系。"
        },
        {
            "question": "性传播疾病有哪些?",
            "answer": "常见的性传播疾病包括艾滋病（HIV/AIDS）、梅毒、淋病、生殖器疱疹（HSV）、尖锐湿疣（HPV）等。"
        },
        {
            "question": "如何预防性病?",
            "answer": "预防性病的方法包括使用避孕套、定期进行性病检查、避免多个性伴侣、保持良好的个人卫生等。"
        },
        {
            "question": "什么是避孕?",
            "answer": "避孕是指采取措施防止怀孕的行为，常见的避孕方法包括避孕套、口服避孕药、宫内节育器等。"
        },
        {
            "question": "避孕有哪些方法?",
            "answer": "常见的避孕方法包括避孕套、口服避孕药、宫内节育器、避孕贴片、避孕针、避孕环等。"
        },
        {
            "question": "什么是月经?",
            "answer": "月经是指女性子宫内膜周期性脱落并排出体外的现象，通常每月一次。"
        },
        {
            "question": "月经周期有多长?",
            "answer": "月经周期通常为21到35天，平均为28天。"
        },
        {
            "question": "什么是更年期?",
            "answer": "更年期是指女性卵巢功能逐渐减退，最终停止排卵的过渡期，通常发生在45到55岁之间。"
        },
        {
            "question": "更年期有哪些症状?",
            "answer": "更年期常见的症状包括潮热、出汗、情绪波动、失眠、记忆力减退、性欲减退等。"
        },
        {
            "question": "什么是性健康?",
            "answer": "性健康是指在身体、情感、社会和精神方面都处于良好的性状态，包括性知识、性行为和性关系的健康。"
        },
        {
            "question": "性健康的重要性是什么?",
            "answer": "性健康的重要性在于促进个人的整体健康，提高生活质量，预防性病和意外怀孕，建立健康的性观念和关系。"
        },
        {
            "question": "性健康包括哪些方面?",
            "answer": "性健康包括性知识、性行为、性关系、性心理和性社会健康等方面。"
        },
        {
            "question": "性健康教育有哪些内容?",
            "answer": "性健康教育的内容包括性知识、性行为、性关系、性心理、性社会健康、性病预防、避孕方法等。"
        },
        {
            "question": "性健康教育的重要性是什么?",
            "answer": "性健康教育的重要性在于帮助人们了解性知识，预防性病和意外怀孕，建立健康的性观念和关系，提高生活质量。"
        },
        {
            "question": "性健康教育的目标是什么?",
            "answer": "性健康教育的目标是提高人们的性知识水平，预防性病和意外怀孕，建立健康的性观念和关系，促进个人和社会的健康。"
        },
        {
            "question": "性健康教育的对象是谁?",
            "answer": "性健康教育的对象包括青少年、成年人和老年人，特别是需要性健康知识的人群。"
        },
        {
            "question": "性健康教育的方式有哪些?",
            "answer": "性健康教育的方式包括课堂教学、讲座、研讨会、媒体宣传、社区活动等。"
        },
        {
            "question": "性健康教育的效果如何评估?",
            "answer": "性健康教育的效果可以通过问卷调查、行为改变、知识测试等方式进行评估。"
        },
        {
            "question": "性健康教育的挑战有哪些?",
            "answer": "性健康教育的挑战包括文化差异、社会观念、隐私问题、资源限制等。"
        },
        {
            "question": "性健康教育的未来趋势是什么?",
            "answer": "性健康教育的未来趋势包括数字化教育、个性化教育、跨学科合作等。"
        }
    ]

    for qa in questions_and_answers:
        try:
            question, created = AIQuestion.objects.get_or_create(question_text=qa["question"])
            if created:
                print(f"插入问题: {question.question_text}")
            else:
                print(f"问题已存在: {question.question_text}")

            AIAnswer.objects.update_or_create(question=question, defaults={"answer_text": qa["answer"]})
            print(f"插入/更新答案: {qa['answer']}")
        except Exception as e:
            print(f"插入问题 {qa['question']} 时出错: {e}")

    print("所有数据插入/更新成功")


if __name__ == "__main__":
    insert_data()
