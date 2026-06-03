<?php
namespace DAC\Core;

class Module_Registry {
	private static array $modules = [];
	private static bool $discovered = false;

	const MODULES_DIR = DIVI_AGENTIC_CORE_DIR . '/modules';

	public static function init(): void {
		add_action( 'init', [ self::class, 'register_blocks' ] );
		add_action( 'wp_enqueue_scripts', [ self::class, 'enqueue_assets' ] );
	}

	public static function discover(): void {
		if ( self::$discovered ) return;
		self::$discovered = true;

		$dirs = glob( self::MODULES_DIR . '/*', GLOB_ONLYDIR );
		if ( ! $dirs ) return;

		foreach ( $dirs as $dir ) {
			$name   = basename( $dir );
			$meta   = null;
			$type   = 'enhancer';
			$slug   = 'dac/' . $name;
			$title  = $name;

			$module_json = $dir . '/module.json';
			$manifest    = $dir . '/manifest.json';

			if ( file_exists( $module_json ) ) {
				$meta  = json_decode( file_get_contents( $module_json ), true ) ?? [];
				$slug  = $meta['name'] ?? $slug;
				$title = $meta['title'] ?? $title;
				$type  = 'block';
			} elseif ( file_exists( $manifest ) ) {
				$meta  = json_decode( file_get_contents( $manifest ), true ) ?? [];
				$slug  = $meta['name'] ?? $slug;
				$title = $meta['title'] ?? $title;
				$type  = $meta['type'] ?? 'enhancer';
			} else {
				continue;
			}

			self::$modules[ $name ] = [
				'name'      => $name,
				'slug'      => $slug,
				'title'     => $title,
				'type'      => $type,
				'dir'       => $dir,
				'meta'      => $meta,
				'render'    => file_exists( $dir . '/render.php' ) ? $dir . '/render.php' : null,
				'style'     => file_exists( $dir . '/style.css' ) ? $dir . '/style.css' : null,
				'editor_css'=> file_exists( $dir . '/editor.css' ) ? $dir . '/editor.css' : null,
				'script'    => file_exists( $dir . '/view.js' ) ? $dir . '/view.js' : null,
			];
		}
	}

	public static function get_all(): array {
		self::discover();
		return self::$modules;
	}

	public static function get( string $name ): ?array {
		self::discover();
		return self::$modules[ $name ] ?? null;
	}

	public static function get_by_slug( string $slug ): ?array {
		self::discover();
		foreach ( self::$modules as $mod ) {
			if ( $mod['slug'] === $slug ) return $mod;
		}
		return null;
	}

	public static function get_allowed_blocks(): array {
		self::discover();
		$blocks = [];
		foreach ( self::$modules as $mod ) {
			if ( $mod['type'] === 'block' ) {
				$blocks[] = $mod['slug'];
			}
		}
		return $blocks;
	}

	public static function register_blocks(): void {
		self::discover();
		foreach ( self::$modules as $mod ) {
			if ( $mod['type'] !== 'block' ) continue;

			register_block_type( $mod['slug'], [
				'render_callback' => function ( $attrs, $content, $block ) use ( $mod ) {
					if ( ! $mod['render'] ) return '';
					$block_attrs = $attrs;
					$block_content = $content;
					ob_start();
					include $mod['render'];
					return ob_get_clean();
				},
			] );
		}
	}

	public static function enqueue_assets(): void {
		self::discover();
		$ds_dep = wp_style_is( 'daw-design-tokens', 'registered' ) ? [ 'daw-design-tokens' ] : [];

		foreach ( self::$modules as $mod ) {

			// ── Block modules: enqueue style.css + view.js ──
			if ( $mod['type'] === 'block' ) {
				$block_handle = 'dac-block-' . $mod['name'];

				if ( $mod['style'] ) {
					wp_register_style( $block_handle, false, $ds_dep, DIVI_AGENTIC_CORE_VERSION );
					wp_enqueue_style( $block_handle );
					wp_add_inline_style( $block_handle, file_get_contents( $mod['style'] ) );
				}

				if ( $mod['editor_css'] ) {
					add_editor_style( $mod['editor_css'] );
				}

				if ( $mod['script'] ) {
					wp_register_script( $block_handle . '-js', false, [], DIVI_AGENTIC_CORE_VERSION, true );
					wp_enqueue_script( $block_handle . '-js' );
					wp_add_inline_script( $block_handle . '-js', file_get_contents( $mod['script'] ) );
				}
			}

			// ── Enhancer modules: enqueue files declared in manifest ──
			if ( $mod['type'] === 'enhancer' ) {
				$manifest = $mod['meta'];
				$requires = $manifest['requires'] ?? [];
				$deps = $ds_dep;
				foreach ( $requires as $dep ) {
					if ( wp_style_is( $dep, 'registered' ) ) {
						$deps[] = $dep;
					}
				}

				$enh_handle = 'dac-enhancer-' . $mod['name'];

				$styles = $manifest['styles'] ?? [];
				foreach ( $styles as $s ) {
					$path = $mod['dir'] . '/' . $s;
					if ( ! file_exists( $path ) ) continue;
					wp_register_style( $enh_handle, false, $deps, DIVI_AGENTIC_CORE_VERSION );
					wp_enqueue_style( $enh_handle );
					wp_add_inline_style( $enh_handle, file_get_contents( $path ) );
				}

				$scripts = $manifest['scripts'] ?? [];
				foreach ( $scripts as $js ) {
					$path = $mod['dir'] . '/' . $js['src'];
					if ( ! file_exists( $path ) ) continue;
					wp_register_script( $enh_handle . '-js', false, [], DIVI_AGENTIC_CORE_VERSION, true );
					wp_enqueue_script( $enh_handle . '-js' );
					wp_add_inline_script( $enh_handle . '-js', file_get_contents( $path ) );
				}
			}
		}
	}

	public static function get_schema( string $slug ): ?array {
		$mod = self::get_by_slug( $slug );
		if ( ! $mod || $mod['type'] !== 'block' ) return null;

		$meta  = $mod['meta'];
		$attrs = [];

		foreach ( ( $meta['attributes'] ?? [] ) as $attr_name => $attr_def ) {
			$default = $attr_def['default'] ?? '';
			$use_inner = isset( $attr_def['settings']['innerContent'] )
				|| isset( $attr_def['settings']['advanced'] );

			if ( $use_inner && isset( $attr_def['settings']['innerContent'] ) ) {
				$attrs[ $attr_name ] = [
					'innerContent' => [
						'desktop' => [ 'value' => $default ],
					],
				];
			} elseif ( $use_inner && isset( $attr_def['settings']['advanced'] ) ) {
				$attrs[ $attr_name ] = [
					'advanced' => [
						'desktop' => [ 'value' => $default ],
					],
				];
			} else {
				$attrs[ $attr_name ] = $default;
			}
		}

		return [
			'block' => [
				'name'  => $slug,
				'attrs' => $attrs,
			],
		];
	}

	public static function get_all_css(): string {
		self::discover();
		$css_parts = [];
		foreach ( self::$modules as $mod ) {
			if ( ! empty( $mod['style'] ) && file_exists( $mod['style'] ) ) {
				$css = file_get_contents( $mod['style'] );
				if ( $css ) {
					$css_parts[] = "/* Module: {$mod['slug']} */\n" . $css;
				}
			}
		}
		return implode( "\n\n", $css_parts );
	}

	public static function get_module_css( string $slug, string $layout = '' ): string {
		$mod = self::get_by_slug( $slug );
		if ( ! $mod ) return '';

		$parts = [];
		$base = $mod['dir'] . '/base.css';
		if ( file_exists( $base ) ) {
			$parts[] = file_get_contents( $base );
		}
		if ( $layout !== '' ) {
			$layout_css = $mod['dir'] . '/layout-' . $layout . '.css';
			if ( file_exists( $layout_css ) ) {
				$parts[] = file_get_contents( $layout_css );
			}
		}
		if ( empty( $parts ) && file_exists( $mod['style'] ) ) {
			$parts[] = file_get_contents( $mod['style'] );
		}
		return implode( "\n", $parts );
	}
}