<?php
/**
 * Export all WPRM recipes + parent post content as JSON.
 * Run via: wp --allow-root eval-file export-recipes.php
 */

$output = [];

// Get all published blog posts
$posts = get_posts([
    'post_type'   => 'post',
    'post_status' => 'publish',
    'numberposts' => -1,
]);

foreach ($posts as $post) {
    // Find WPRM recipe ID — two formats: shortcode or HTML comment
    $recipe_id = null;
    if (preg_match('/\[wprm-recipe id="?(\d+)"?\]/', $post->post_content, $m)) {
        $recipe_id = $m[1];
    } elseif (preg_match('/<!--WPRM Recipe (\d+)-->/', $post->post_content, $m)) {
        $recipe_id = $m[1];
    }

    $recipe_data = null;
    if ($recipe_id) {
        $recipe = WPRM_Recipe_Manager::get_recipe(intval($recipe_id));
        if ($recipe) {
            $image_url = '';
            if ($recipe->image_id()) {
                $image_url = wp_get_attachment_url($recipe->image_id());
            }

            $recipe_data = [
                'id'            => $recipe->id(),
                'name'          => $recipe->name(),
                'summary'       => $recipe->summary(),
                'prep_time'     => $recipe->prep_time(),
                'cook_time'     => $recipe->cook_time(),
                'total_time'    => $recipe->total_time(),
                'servings'      => $recipe->servings(),
                'servings_unit' => $recipe->servings_unit(),
                'ingredients'   => $recipe->ingredients(),
                'instructions'  => $recipe->instructions(),
                'nutrition'     => $recipe->nutrition(),
                'image_id'      => $recipe->image_id(),
                'image_url'     => $image_url,
            ];
        }
    }

    // Get post featured image
    $post_image_url = get_the_post_thumbnail_url($post->ID, 'full') ?: '';

    // Get categories and tags
    $categories = wp_get_post_categories($post->ID, ['fields' => 'all']);
    $tags = wp_get_post_tags($post->ID, ['fields' => 'all']);

    // Strip recipe embed and fallback HTML from post content to get narrative only
    $narrative = $post->post_content;
    $narrative = preg_replace('/\[wprm-recipe id="?\d+"?\]/', '', $narrative);
    $narrative = preg_replace('/<!--WPRM Recipe \d+-->/', '', $narrative);
    $narrative = preg_replace('/<div class="wprm-fallback-recipe">.*?<\/div>\s*<\/div>/s', '', $narrative);
    $narrative = trim($narrative);

    $output[] = [
        'post_id'        => $post->ID,
        'post_title'     => $post->post_title,
        'post_slug'      => $post->post_name,
        'post_date'      => $post->post_date,
        'post_content'   => $narrative,
        'post_image_url' => $post_image_url,
        'categories'     => array_map(function($c) {
            return ['id' => $c->term_id, 'name' => $c->name, 'slug' => $c->slug];
        }, $categories),
        'tags'           => array_map(function($t) {
            return ['id' => $t->term_id, 'name' => $t->name, 'slug' => $t->slug];
        }, $tags),
        'recipe'         => $recipe_data,
    ];
}

// Also export pages
$pages = get_posts([
    'post_type'   => 'page',
    'post_status' => 'publish',
    'numberposts' => -1,
]);

$pages_output = [];
foreach ($pages as $page) {
    $pages_output[] = [
        'id'      => $page->ID,
        'title'   => $page->post_title,
        'slug'    => $page->post_name,
        'content' => $page->post_content,
    ];
}

echo json_encode([
    'recipes' => $output,
    'pages'   => $pages_output,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
