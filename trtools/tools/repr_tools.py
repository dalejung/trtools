def base_repr(obj, attrs, class_name=None):

    if not class_name:
        class_name = obj.__class__.__name__
    ns = {'class_name':class_name}

    string = ""
    bits = []
    for attr in attrs:
        process_attr(obj, ns, bits, attr)

    #if hasattr(obj,'gen_id'):
    #    process_attr(obj, ns, bits, 'gen_id')

    string = "{class_name}("+','.join(bits)+")"
    return string.format(**ns)

def process_attr(obj, ns, bits, attr, value=None):
    try:
        if value is None:
            value = getattr(obj, attr)
        ns[attr] = value
        bits.append('{attr}={{{attr}}}'.format(attr=attr))
    except AttributeError:
        pass
