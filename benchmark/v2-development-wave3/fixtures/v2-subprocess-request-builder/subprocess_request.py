def build_request(template, values, base_env):
    argv = [part.format(**values) for part in template["argv"]]
    env = dict(base_env)
    env.update({name: value.format(**values) for name, value in template.get("env", {}).items()})
    return {"argv": argv, "env": env, "cwd": template.get("cwd")}
