"""Tạo ZIP snapshot chưa commit và kiểm chạy sau giải nén; không thay git archive từ tag."""
from pathlib import Path
import subprocess
import tempfile
import zipfile

from proof_clean_clone import smoke

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'chonoi-v1.0.0-preview.zip'
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=ROOT).decode('utf-8').split('\0')
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(names)):
            path = ROOT / name
            if not name or path == output or not path.is_file() or name.startswith('.p4-day-ui-check-'):
                continue
            archive.write(path, 'chonoi-v1.0.0/' + name)
    with tempfile.TemporaryDirectory(prefix='.p4-day-ui-check-', dir=ROOT) as temp:
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            archive.extractall(temp)
        print('PREVIEW ZIP', output.name, smoke(Path(temp) / 'chonoi-v1.0.0'))
    print('ZIP integrity OK; temporary extraction cleaned; official Release still needs git archive from tag.')


if __name__ == '__main__':
    main()
