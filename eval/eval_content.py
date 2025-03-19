from pathlib import Path

from numpy import mean
from tenacity import retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

FILE_PATH = Path(__file__).absolute()
BASE_DIR = FILE_PATH.parent

from utils import remote_chat, load_file_as_string

TOPICS = """In-context Learning
Out-of-Distribution Detection
Semi-Supervised Learning
LLMs for Recommendation
LLM-Generated Texts Detection
Explainability for LLMs
Evaluation of LLMs
LLMs-based Agents
LLMs in Medicine
Domain Specialization of LLMs
Challenges of LLMs in Education
Alignment of LLMs
ChatGPT
Instruction Tuning for LLMs
LLMs for Information Retrieval
Safety in LLMs
Chain of Thought
Hallucination in LLMs
Bias and Fairness in LLMs
Large Multi-Modal Language Models
Acceleration for LLMs
LLMs for Software Engineering
""".splitlines()

svx_path = Path(f"{BASE_DIR}/data/svx")
# print(remote_chat("hello"))

prompt_for_content = {
    "coverage": """Here is an academic survey about the topic "{topic}":
---
{content}
---

<instruction>
Please evaluate this survey about the topic {topic} based on the criterion above provided below, and give a score from 1 to 5 according to the score description:
---
Criterion Description: Coverage: Coverage assesses the extent to which the survey encapsulates all relevant aspects of the topic, ensuring comprehensive discussion on both central and peripheral topics.
---
Score 1 Description: The survey has very limited coverage, only touching on a small portion of the topic and lacking discussion on key areas.
Score 2 Description: The survey covers some parts of the topic but has noticeable omissions, with significant areas either underrepresented or missing.
Score 3 Description: The survey is generally comprehensive in coverage but still misses a few key points that are not fully discussed.
Score 4 Description: The survey covers most key areas of the topic comprehensively, with only very minor topics left out.
Score 5 Description: The survey comprehensively covers all key and peripheral topics, providing detailed discussions and extensive information.
---
Return the score without any other information:

""",
    "structure": """Here is an academic survey about the topic "{topic}":
---
{content} 
---

<instruction>
Please evaluate this survey about the topic {topic} based on the criterion above provided below, and give a score from 1 to 5 according to the score description:
---
Criterion Description: Structure: Structure evaluates the logical organization and coherence of sections and subsections, ensuring that they are logically connected.
---
Score 1 Description: The survey lacks logic, with no clear connections between sections, making it difficult to understand the overall framework.
Score 2 Description: The survey has weak logical flow with some content arranged in a disordered or unreasonable manner.
Score 3 Description: The survey has a generally reasonable logical structure, with most content arranged orderly, though some links and transitions could be improved such as repeated subsections.
Score 4 Description: The survey has good logical consistency, with content well arranged and natural transitions, only slightly rigid in a few parts.
Score 5 Description: The survey is tightly structured and logically clear, with all sections and content arranged most reasonably, and transitions between adajecent sections smooth without redundancy.
---
Return the score without any other information:
""",
    "relevance": """Here is an academic survey about the topic "{topic}":
---
{content}
---

<instruction>
Please evaluate this survey about the topic {topic} based on the criterion above provided below, and give a score from 1 to 5 according to the score description:
---
Criterion Description: Relevance: Relevance measures how well the content of the survey aligns with the research topic and maintain a clear focus.
---
Score 1 Description: The  content is outdated or unrelated to the field it purports to review, offering no alignment with the topic
Score 2 Description: The survey is somewhat on topic but with several digressions; the core subject is evident but not consistently adhered to.
Score 3 Description: The survey is generally on topic, despite a few unrelated details.
Score 4 Description: The survey is mostly on topic and focused; the narrative has a consistent relevance to the core subject with infrequent digressions.
Score 5 Description: The survey is exceptionally focused and entirely on topic; the article is tightly centered on the subject, with every piece of information contributing to a comprehensive understanding of the topic.
---
Return the score without any other information:""",
}

new_content_prompt = {
    "synthesis": """Here is an academic survey about the topic "{topic}":
---
{content}
---

<instruction>
Please evaluate this survey about the topic {topic} based on the criterion above provided below, and give a score from 1 to 5 according to the score description:
---
Criterion Description: Synthesis: Synthesis evaluates the ability to interconnect disparate studies, identify overarching patterns or contradictions, and construct a cohesive intellectual framework beyond individual summaries.
---
Score 1 Description: The survey is purely a collection of isolated study summaries with no attempt to connect ideas or identify broader trends.
Score 2 Description: The survey occasionally links studies but fails to synthesize them into meaningful patterns; connections are superficial.
Score 3 Description: The survey identifies some thematic relationships between studies but lacks a unified framework to explain their significance.
Score 4 Description: The survey synthesizes most studies into coherent themes or debates, though some connections remain underdeveloped.
Score 5 Description: The survey masterfully integrates studies into a novel framework, revealing latent trends, resolving contradictions, and proposing paradigm-shifting perspectives.
---
Return the score without any other information:""",
    "critical_analysis": """Here is an academic survey about the topic "{topic}":
---
{content}
---

<instruction>
Please evaluate this survey about the topic {topic} based on the criterion above provided below, and give a score from 1 to 5 according to the score description:
---
Criterion Description: Critical Analysis: Critical Analysis examines the depth of critique applied to existing studies, including identification of methodological limitations, theoretical inconsistencies, and research gaps.
---
Score 1 Description: The survey merely lists existing studies without any analytical commentary or critique.
Score 2 Description: The survey occasionally mentions limitations of studies but lacks systematic analysis or synthesis of gaps.
Score 3 Description: The survey provides sporadic critical evaluations of some studies, but the critique is shallow or inconsistent.
Score 4 Description: The survey systematically critiques most key studies and identifies research gaps, though some areas lack depth.
Score 5 Description: The survey demonstrates rigorous critical analysis of methodologies and theories, clearly maps research frontiers, and proposes novel directions based on synthesized gaps.
---
Return the score without any other information:""",
}


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
def llm_judge_content(content: str, topic: str, prompt: str) -> int:
    prompt = prompt.format(topic=topic, content=content)
    res = remote_chat(prompt)
    ans = int(res)
    return ans


if __name__ == "__main__":
    res = {}
    bar = tqdm({**prompt_for_content, **new_content_prompt}.items())
    for dim, prompt in bar:
        bar.set_description(f"evaluating {dim}")
        svx_res = []
        for topic in TOPICS:
            svx_file_path = svx_path / f"{topic}.tex"
            svx_content = load_file_as_string(svx_file_path)
            svx_res.append(llm_judge_content(svx_content, topic, prompt))

        res[dim] = svx_res

    for dim, val in res.items():
        print(f"{dim}  {mean(val)}")
