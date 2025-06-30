import json
from django.core.exceptions import ValidationError
from apps.content.models import Subject, Topic

def process_question_form_data(data):
    print('[[[[[]]]]]data]]]]]]]]]]]',data)
    """Process form data for question creation/update."""
    processed_data = data.dict() if hasattr(data, 'dict') else data.copy()
    
    # Handle options
    options = {
        'A': data.get('options.A', '').strip(),
        'B': data.get('options.B', '').strip(),
        'C': data.get('options.C', '').strip(),
        'D': data.get('options.D', '').strip(),
    }
    processed_data['options'] = options
    
    # Handle topics
    topics = data.getlist('topics') if hasattr(data, 'getlist') else data.get('topics', [])
    if isinstance(topics, str):
        processed_data['topics'] = [int(topics)]
    elif isinstance(topics, list):
        processed_data['topics'] = [int(t) for t in topics]
    else:
        processed_data['topics'] = []
    
    # Handle metadata
    metadata_raw = data.get('metadata', '').strip()
    try:
        processed_data['metadata'] = json.loads(metadata_raw) if metadata_raw else {}
    except json.JSONDecodeError:
        processed_data['metadata'] = {}
    
    return processed_data

def get_subject_topic_context(user, subject_id=None):
    """Fetch subjects and topics with optional filtering."""
    subjects = Subject.objects.all()
    topics = Topic.objects.filter(subject_id=subject_id) if subject_id else Topic.objects.all()
    return {'subjects': subjects, 'topics': topics}