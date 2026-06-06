import argparse
import os

from backend.bilinovel.bilinovel_router import downloader_router

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='config')
    parser.add_argument('--interval', default=4500, type=int)
    parser.add_argument('--num_thread', default='1', type=int)
    parser.add_argument('--out_path', default='./out', type=str)
    parser.add_argument(
        '--browser',
        default='auto',
        choices=('auto', 'safari', 'chromium'),
        help='网页浏览器后端；macOS 上 auto 默认使用 Safari',
    )
    parser.add_argument(
        '--browser-path',
        default=None,
        help='Chromium 可执行文件路径，Safari 不需要设置',
    )
    args = parser.parse_args()
    return args


if __name__=='__main__':
    args = parse_args()
    os.makedirs(args.out_path, exist_ok=True)
    while True:
        try:
            book_no = input('请输入书籍号：')
            volume_no = input('请输入卷号(查看目录信息不输入直接按回车，下载多卷请使用逗号分隔或者连字符-)：')
        except EOFError:
            break
        downloader_router(
            root_path=args.out_path,
            book_no=book_no,
            volume_no=volume_no,
            interval=args.interval,
            num_thread=args.num_thread,
            browser=args.browser,
            browser_path=args.browser_path,
        )
        # book_no = '2704'
        # volume_no = '1'
        # downloader_router(root_path=args.out_path, book_no=book_no, volume_no=volume_no, interval=args.interval, num_thread=args.num_thread)
        # exit(0)
