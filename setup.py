setting = {
    'filepath' : __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': None,
    'menu': {
        'uri': __package__,
        'name': '웨이브',
        'list': [
            {
                'uri': 'basic',
                'name': '기본',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'download', 'name': '다운로드'},
                ]
            },
            {
                'uri': 'recent',
                'name': '최근방송 자동',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'list', 'name': '목록'},
                ]
            },
            {
                'uri': 'program',
                'name': '프로그램별 자동',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'select', 'name': '선택'},
                    {'uri': 'queue', 'name': '큐'},
                    {'uri': 'list', 'name': '목록'},
                ]
            },
            {
                'uri': 'log',
                'name': '로그',
            },
        ]
    },
    'default_route': 'normal',
}
from plugin import *

DEFINE_DEV = False
if os.path.exists(os.path.join(os.path.dirname(__file__), 'mod_basic.py')):
    DEFINE_DEV = True

P = create_plugin_instance(setting)
try:
    if DEFINE_DEV:
        from .mod_basic import ModuleBasic
        from .mod_program import ModuleProgram
        from .mod_recent import ModuleRecent
    else:
        from support import SupportSC
        mod_basic = SupportSC.load_module_P(P, 'mod_basic')
        mod_recent = SupportSC.load_module_P(P, 'mod_recent')
        mod_program = SupportSC.load_module_P(P, 'mod_program')
        ModuleBasic = mod_basic.ModuleBasic
        ModuleRecent = mod_recent.ModuleRecent
        ModuleProgram = mod_program.ModuleProgram

        import functools
        def wrap_func(func, new_func):
            @functools.wraps(func)
            def run(*args, **kwargs):
                new_func(*args, **kwargs)
                return func(*args, **kwargs)
            return run

        def after_func(func, new_func):
            @functools.wraps(func)
            def run(*args, **kwargs):
                return new_func(func(*args, **kwargs))
            return run

        def hook_recent(*args, **kwargs):
            P.logger.debug(f'programtitle: {args[0].programtitle}')
            P.logger.debug(f'filename: {args[0].filename}')
            if args[0].filename.startswith('.'):
                args[0].filename = args[0].programtitle + args[0].filename

        def hook_program(*args, **kwargs):
            if args[0].contents_json:
                P.logger.debug(f'programtitle: {args[0].program_title}')
                P.logger.debug(f'seasontitle: {args[0].contents_json["seasontitle"]}')
                if not args[0].program_title:
                    args[0].program_title = args[0].contents_json.get('seasontitle', args[0].contents_json.get('episodetitle', args[0].contents_json['programid']))
                    args[0].contents_json['programtitle'] = args[0].program_title

        def hook_analyze(result):
            if result.get('url_type') == 'episode':
                if not result['episode']['programtitle']:
                    result['episode']['programtitle'] = result['episode']['seasontitle']
                    result['available']['filename'] = result['episode']['programtitle'] + result['available']['filename']
            else:
                pass
                P.logger.debug(result)
            return result

        mod_recent.ModelWavveRecent.save = wrap_func(mod_recent.ModelWavveRecent.save, hook_recent)
        mod_program.ModelWavveProgram.save = wrap_func(mod_program.ModelWavveProgram.save, hook_program)
        mod_basic.ModuleBasic.analyze = after_func(mod_basic.ModuleBasic.analyze, hook_analyze)

        from ffmpeg.custom_ffmpeg import SupportFfmpeg
        mod_program.SupportFfmpeg = SupportFfmpeg
        mod_basic.SupportFfmpeg = SupportFfmpeg
        mod_recent.SupportFfmpeg = SupportFfmpeg
    
    P.set_module_list([ModuleBasic, ModuleRecent, ModuleProgram])
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())
