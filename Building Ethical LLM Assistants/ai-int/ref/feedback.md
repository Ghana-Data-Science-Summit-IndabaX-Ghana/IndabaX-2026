# **Feedback on Building Ethical LLMs**

**Major:**

* There is a need to include a presentation slide. The slide should aim to cover the following:  
  * Fundamentals of LLM assistant within the entire agentic AI landscape  
  * Raise concerns regarding the ethical deployment of LLMs, i.e., data privacy, hallucinations, misuse, etc  
  * In addition, the example of representation bias in the Ghanaian context could be made more explicit. For example, using under representation of women in the legislative arm of government.  
    

**PS:** I believe some aspects of what should go into the slide are already included in the “Building Ethical LLM Assistants Outline.pdf.” You would need to carefully carve these out and make some nice slides to guide this aspect of the tutorial.

* I looked into the code subfolder, too. First, I did not run the entire notebook to see if it runs without any errors from top to bottom. However, I am unable to see the full goal/takeaway of the notebook.  
  * If we are already providing a notebook, there is no need to have a  build\_notebook.py to generate a notebook already available. I would suggest this script be removed.  
* The ethical\_llm\_workshop.ipynb does not include any implementation of the guardrails as mentioned in the outline.   
* In addition, it would be helpful to guide participants on the need for developing an RAG assistant AI.   
* The notebook would benefit from being reorganized into two or three broader sections. In its current form, it is divided into many very small parts, which makes the overall structure feel fragmented and makes it harder to see how the ideas connect. I would reorganize the notebook into three broader sections: (i) motivation and setup, (ii) implementation of the assistants, and (iii) guardrails or safety-based techniques. This would make the tutorial easier to follow and help participants.  
* Remove teaching notes from the participants' notebooks and include only explanations that support understanding. If teaching notes are needed, create two versions: an instructor notebook with facilitation guidance and a participant notebook with only the relevant explanations, code, examples, and exercises.

**Minor:**

* The tutorial contains PDFs with an outline and notes, with a subfolder with code. I presumed the PDF with the note is supposed to guide the flow of the presentations. This, I believe, should not be kept in the entire tutorial folder.   
* Kindly do not forget to complete your details at the end of the notebook  
   (see screenshot)   
  


**Overall thought:** The broad skeleton structure of the tutorial is good; however, it would help greatly to carefully read and ensure coherence of materials.  I also like that the text examples are based on a Ghanaian context, something participants can easily relate to.  
Finally, while the use of LLMs to generate materials is **definitely acceptable,** it would be appreciated if all generated content were carefully reviewed. This would help ensure that the final tutorial materials are coherent, accurate, and aligned with the tutorial’s overall goals.