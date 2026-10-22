"""MySQL 驱动兼容层。

优先使用 mysqlclient（C 扩展，快）。若本机无法编译 mysqlclient 而改装了 PyMySQL，
本模块会自动把 PyMySQL 注册成 MySQLdb 并修正版本号，避免 Django 报
"mysqlclient 1.4.3 or newer is required"。
"""

try:  # pragma: no cover
    import MySQLdb  # noqa: F401
except ImportError:  # pragma: no cover
    try:
        import pymysql

        pymysql.version_info = (1, 4, 6, "final", 0)
        pymysql.install_as_MySQLdb()
    except ImportError:
        # 既没装 mysqlclient 也没装 PyMySQL 时交给 Django 自己报错；
        # 若使用 sqlite 验证则完全不需要驱动。
        pass
