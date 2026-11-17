import main


def touch(d, name):
    p = d / name
    p.write_bytes(b"x")
    return str(p)


def test_scene_naming_variants(tmp_path):
    a = touch(tmp_path, "scene01.png")
    b = touch(tmp_path, "scene_02.png")
    c = touch(tmp_path, "tb_03.png")
    assert main.find_scene_files(str(tmp_path), 1, ["png"]) == [a]
    assert main.find_scene_files(str(tmp_path), 2, ["png"]) == [b]
    assert main.find_scene_files(str(tmp_path), 3, ["png"]) == [c]
    assert main.find_scene_files(str(tmp_path), 4, ["png"]) == []
    assert main.find_scene_file(str(tmp_path), 4, ["png"]) is None


def test_multiple_images_per_scene_are_sorted(tmp_path):
    second = touch(tmp_path, "tb_14_2.png")
    first = touch(tmp_path, "tb_14_1.png")
    assert main.find_scene_files(str(tmp_path), 14, ["png"]) == [first, second]


def test_exact_match_beats_variants(tmp_path):
    exact = touch(tmp_path, "scene05.png")
    touch(tmp_path, "scene05_alt.png")
    assert main.find_scene_files(str(tmp_path), 5, ["png"]) == [exact]


def test_scene01_does_not_match_scene010(tmp_path):
    touch(tmp_path, "scene010.png")
    assert main.find_scene_files(str(tmp_path), 1, ["png"]) == []


def test_non_matching_extensions_ignored(tmp_path):
    touch(tmp_path, "tb_07_notes.txt")
    jpg = touch(tmp_path, "tb_07_a.JPG")
    assert main.find_scene_files(str(tmp_path), 7, ["png", "jpg"]) == [jpg]
