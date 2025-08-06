#!/usr/bin/env python
"""src/utils/__init__.py

Utility functions for the family doctor assistant.
"""

from .transliteration import transliterate_ukrainian

def extract_patient_response(full_diagnosis: str) -> str:
    """
    Extract the "Коротка відповідь для пацієнта" section from the full diagnosis.
    
    Args:
        full_diagnosis: The complete diagnosis response from RAG
        
    Returns:
        The patient response section, or a simplified version if section not found
    """
    import re
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Look for the patient response section with multiple possible patterns
    patterns = [
        # Pattern 1: Standard format with emoji
        r'##\s*✍️\s*1\.\s*Коротка\s*відповідь\s*для\s*пацієнта.*?(?=\n##|\Z)',
        # Pattern 2: Without emoji
        r'##\s*1\.\s*Коротка\s*відповідь\s*для\s*пацієнта.*?(?=\n##|\Z)',
        # Pattern 3: Just the header without numbering
        r'##\s*Коротка\s*відповідь\s*для\s*пацієнта.*?(?=\n##|\Z)',
        # Pattern 4: Look for any section that mentions "пацієнта" or "пацієнт"
        r'##.*?пацієнт.*?(?=\n##|\Z)',
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, full_diagnosis, re.DOTALL | re.IGNORECASE)
        if match:
            # Extract the matched section and clean it up
            patient_section = match.group(0).strip()
            
            # Remove the header line and clean up formatting
            lines = patient_section.split('\n')
            if lines and any(keyword in lines[0].lower() for keyword in ['коротка відповідь', 'пацієнт']):
                # Remove the header line
                lines = lines[1:]
            
            # Join lines and clean up
            patient_response = '\n'.join(lines).strip()
            
            # If we got a meaningful response, return it
            if patient_response and len(patient_response) > 10:
                logger.info(f"Successfully extracted patient response using pattern {i+1}")
                return patient_response
    
    # If no patient section found, try to extract a simplified version
    logger.warning("No patient response section found, creating simplified version")
    
    # Look for the first paragraph or section that might be patient-friendly
    # Split by double newlines to find sections
    sections = full_diagnosis.split('\n\n')
    
    for section in sections:
        section = section.strip()
        # Skip sections that are clearly for doctors
        if any(keyword in section.lower() for keyword in ['лікар', 'професійна', 'діагноз', 'обстеження', 'лікування']):
            continue
        
        # Look for sections that might be patient-friendly
        if len(section) > 20 and len(section) < 500:  # Reasonable length for patient response
            # Remove markdown formatting
            clean_section = re.sub(r'^#+\s*', '', section)  # Remove headers
            clean_section = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_section)  # Remove bold
            clean_section = re.sub(r'\*(.*?)\*', r'\1', clean_section)  # Remove italic
            
            if clean_section and len(clean_section) > 20:
                logger.info("Created simplified patient response from first suitable section")
                return clean_section
    
    # Final fallback: return a very short version of the full diagnosis
    logger.warning("Using fallback: creating minimal patient response")
    
    # Take the first few sentences that don't contain medical jargon
    sentences = re.split(r'[.!?]+', full_diagnosis)
    patient_sentences = []
    
    # Medical keywords to avoid
    medical_keywords = [
        'діагноз', 'обстеження', 'лікування', 'протокол', 'клінічний', 
        'анамнез', 'диференційна', 'неврологічне', 'рентгенографія',
        'м\'язово-скелетних', 'симптоми', 'ознак', 'порушень', 'причин',
        'за потреби', 'рекомендацією лікаря', 'контроль за симптомами',
        'оцінка стану', 'протоколами МОЗ', 'базується на анамнезі',
        'клінічному обстеженні', 'диференціювати', 'мігрені', 'вторинні причини',
        'переважно немедикаментозне', 'профілактику', 'зняття м\'язов'
    ]
    
    # Keywords that indicate the sentence is for doctors (avoid these)
    doctor_keywords = ['лікар', 'професійна', 'діагноз', 'обстеження', 'лікування']
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Skip sentences with too much medical jargon
        if any(keyword in sentence.lower() for keyword in medical_keywords):
            continue
            
        # Skip sentences that are clearly for doctors
        if any(keyword in sentence.lower() for keyword in doctor_keywords):
            continue
            
        # Skip very short sentences
        if len(sentence) < 10:
            continue
            
        # Skip sentences that are just lists or bullet points
        if sentence.startswith('-') or sentence.startswith('•'):
            continue
            
        patient_sentences.append(sentence)
        
        # Stop after 2-3 sentences
        if len(patient_sentences) >= 3:
            break
    
    if patient_sentences:
        fallback_response = '. '.join(patient_sentences) + '.'
        logger.info("Created fallback patient response from filtered sentences")
        return fallback_response
    
    # If we still don't have a good response, create a generic one based on the content
    logger.warning("No suitable sentences found, creating generic response")
    
    # Look for any positive or helpful content
    helpful_keywords = ['рекомендується', 'можна', 'варто', 'корисно', 'допоможе', 'важливо']
    for sentence in sentences:
        sentence = sentence.strip()
        if any(keyword in sentence.lower() for keyword in helpful_keywords):
            # Clean up the sentence
            clean_sentence = re.sub(r'^[-•]\s*', '', sentence)  # Remove bullet points
            clean_sentence = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_sentence)  # Remove bold
            clean_sentence = re.sub(r'\*(.*?)\*', r'\1', clean_sentence)  # Remove italic
            
            if len(clean_sentence) > 15 and len(clean_sentence) < 200:
                logger.info("Created generic response from helpful content")
                return clean_sentence + '.'
    
    # Try to extract any sentence that doesn't contain heavy medical terms
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 15:
            continue
            
        # Skip if it contains too many medical terms
        medical_term_count = sum(1 for keyword in medical_keywords if keyword in sentence.lower())
        if medical_term_count > 2:  # Allow some medical terms but not too many
            continue
            
        # Clean up the sentence
        clean_sentence = re.sub(r'^[-•]\s*', '', sentence)  # Remove bullet points
        clean_sentence = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_sentence)  # Remove bold
        clean_sentence = re.sub(r'\*(.*?)\*', r'\1', clean_sentence)  # Remove italic
        
        if len(clean_sentence) > 15:
            logger.info("Created response from sentence with minimal medical terms")
            return clean_sentence + '.'
    
    # Last resort: return a generic message
    logger.error("Could not extract any patient-friendly content")
    return "Ваш запит оброблено. Будь ласка, зверніться до лікаря для детальної консультації."

__all__ = ["transliterate_ukrainian", "extract_patient_response"] 