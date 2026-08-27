from blog.post import Post, to_url_key


def test_to_url_key_folds_separators_and_lowercases() -> None:
    assert to_url_key("Hello  World!") == "hello-world"
    assert to_url_key("  --Draft--  ") == "draft"


def test_to_url_key_falls_back_for_empty_titles() -> None:
    assert to_url_key("!!!") == "untitled"
    assert to_url_key("") == "untitled"


def test_post_path_uses_project_convention() -> None:
    assert Post("My First Post").path == "/blog/my-first-post"
