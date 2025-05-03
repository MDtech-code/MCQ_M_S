from datetime import datetime

def global_context(request):
    return {
        'now': datetime.now()
    }
