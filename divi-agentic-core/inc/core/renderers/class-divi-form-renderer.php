<?php
/**
 * Renderer: Divi Form
 *
 * Handles contact-form, contact-field, login, subscribe, search.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Form_Renderer
 */
class Divi_Form_Renderer extends Divi_Base_Renderer {

	/**
	 * Safely retrieve a nested array value.
	 *
	 * @param array  $arr     Source array.
	 * @param string ...$keys Keys to traverse.
	 * @return mixed|null Value or null if path missing.
	 */
	private function get_nested( array $arr, ...$keys ) {
		foreach ( $keys as $key ) {
			if ( ! is_array( $arr ) || ! isset( $arr[ $key ] ) ) {
				return null;
			}
			$arr = $arr[ $key ];
		}
		return $arr;
	}

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs      = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? '5.7.4' );
		$inner_html = '';

		switch ( $slug ) {
			case 'divi/contact-form':
		// Preserve fully-qualified attrs if already provided.
		foreach ( [ 'email', 'button', 'messageSuccess', 'form', 'fieldItem', 'module' ] as $top_key ) {
			if ( isset( $data[ $top_key ] ) ) {
				$attrs[ $top_key ] = array_replace_recursive( $attrs[ $top_key ] ?? [], $data[ $top_key ] );
			}
		}

				// Resolve email receiver from shorthand or nested sources.
				if ( ! isset( $attrs['email']['advanced']['receiver']['desktop']['value'] ) ) {
					$receiver = $data['email_to']
						?? $this->get_nested( $data, 'email', 'advanced', 'receiver', 'desktop', 'value' )
						?? $this->get_nested( $data, 'module', 'advanced', 'receiver', 'desktop', 'value' )
						?? null;

					if ( null !== $receiver && '' !== $receiver ) {
						if ( ! isset( $attrs['email'] ) ) {
							$attrs['email'] = [];
						}
						if ( ! isset( $attrs['email']['innerContent'] ) ) {
							$attrs['email']['innerContent'] = [ 'desktop' => [ 'value' => '' ] ];
						}
						$attrs['email']['advanced']['receiver']['desktop']['value'] = $receiver;
					}
				}

				// Resolve submit button text.
				if ( ! isset( $attrs['button']['innerContent']['desktop']['value']['text'] ) ) {
					$submit_text = $data['submit_text']
						?? $this->get_nested( $data, 'button', 'innerContent', 'desktop', 'value', 'text' )
						?? null;

					if ( null !== $submit_text && '' !== $submit_text ) {
						$attrs['button']['innerContent'] = [
							'desktop' => [ 'value' => [ 'text' => $submit_text ] ],
						];
					}
				}

				// Resolve contact-form title (Divi 5 native structure).
				if ( ! isset( $attrs['title']['innerContent']['desktop']['value'] ) ) {
					$form_title = $data['title_text']
						?? $data['title']
						?? $this->get_nested( $data, 'title', 'innerContent', 'desktop', 'value' )
						?? null;

					if ( is_array( $form_title ) && isset( $form_title['innerContent']['desktop']['value'] ) ) {
						$form_title = $form_title['innerContent']['desktop']['value'];
					}

					if ( null !== $form_title && '' !== $form_title ) {
						$attrs['title']['innerContent'] = [
							'desktop' => [ 'value' => $form_title ],
						];
					}

					// Preserve title.decoration.font from input data if provided.
					$title_decoration = $this->get_nested( $data, 'title', 'decoration' );
					if ( is_array( $title_decoration ) ) {
						$attrs['title']['decoration'] = $title_decoration;
					}
				}

				// Resolve success message.
				if ( ! isset( $attrs['messageSuccess']['innerContent']['desktop']['value'] ) ) {
					$success_message = $data['success_message']
						?? $this->get_nested( $data, 'messageSuccess', 'innerContent', 'desktop', 'value' )
						?? $this->get_nested( $data, 'module', 'advanced', 'successMessage', 'desktop', 'value' )
						?? $this->get_nested( $data, 'module', 'advanced', 'messageSuccess', 'desktop', 'value' )
						?? null;

					if ( null !== $success_message && '' !== $success_message ) {
						$attrs['messageSuccess']['innerContent'] = [
							'desktop' => [ 'value' => $success_message ],
						];
					}
				}

			if ( isset( $data['use_captcha'] ) ) {
				$attrs['module']['advanced']['spamProtection']['desktop']['value'] = [
					'enabled'         => $data['use_captcha'] ? 'on' : 'off',
					'useBasicCaptcha' => $data['use_captcha'] ? 'on' : 'off',
				];
			}

			// Preserve top-level form spacing / formGap settings.
			if ( isset( $data['form'] ) && ! isset( $attrs['form'] ) ) {
				$attrs['form'] = $data['form'];
			}

			$inner_html = $children_html;
			break;

			case 'divi/contact-field':
		// Preserve fully-qualified fieldItem if already provided.
		if ( isset( $data['fieldItem'] ) ) {
			$attrs['fieldItem'] = array_replace_recursive( $attrs['fieldItem'] ?? [], $data['fieldItem'] );
		}

		// Preserve fieldItem decoration/placeholder/selectOptions from data keys.
		foreach ( [ 'font', 'decoration' ] as $fik ) {
			if ( isset( $data['fieldItem'][ $fik ] ) && ! isset( $attrs['fieldItem'][ $fik ] ) ) {
				$attrs['fieldItem'][ $fik ] = $data['fieldItem'][ $fik ];
			}
		}

		// Build from shorthand keys when fieldItem is incomplete.
		if ( ! isset( $attrs['fieldItem']['innerContent']['desktop']['value'] ) ) {
					$field_label = $data['field_label']
						?? $this->get_nested( $data, 'fieldItem', 'innerContent', 'desktop', 'value' )
						?? null;
					$field_type  = $data['field_type']
						?? $this->get_nested( $data, 'fieldItem', 'advanced', 'type', 'desktop', 'value' )
						?? null;

					if ( null !== $field_type && null !== $field_label ) {
						$field_id = isset( $data['field_id'] ) && '' !== $data['field_id']
							? $data['field_id']
							: $this->get_nested( $data, 'fieldItem', 'advanced', 'id', 'desktop', 'value' )
								?? sanitize_title( $field_label );

						$attrs['fieldItem']['advanced']['type']['desktop']['value']     = $field_type;
						$attrs['fieldItem']['advanced']['id']['desktop']['value']       = $field_id;
						$attrs['fieldItem']['innerContent']['desktop']['value']       = $field_label;

						if ( ! isset( $attrs['fieldItem']['advanced']['required']['desktop']['value'] ) ) {
							$required = $data['required']
								?? $this->get_nested( $data, 'fieldItem', 'advanced', 'required', 'desktop', 'value' )
								?? false;
							$attrs['fieldItem']['advanced']['required']['desktop']['value'] = ( $required && 'off' !== $required ) ? 'on' : 'off';
						}
					}
				}

				// Fullwidth.
				if ( ! isset( $attrs['fieldItem']['advanced']['fullwidth']['desktop']['value'] ) ) {
					$fullwidth = $data['fullwidth']
						?? $this->get_nested( $data, 'fieldItem', 'advanced', 'fullwidth', 'desktop', 'value' )
						?? null;
					if ( null !== $fullwidth ) {
						$attrs['fieldItem']['advanced']['fullwidth']['desktop']['value'] = ( $fullwidth && 'off' !== $fullwidth ) ? 'on' : 'off';
					}
				}

				// Placeholder.
				if ( ! isset( $attrs['fieldItemPlaceholder']['desktop']['value'] ) ) {
					$placeholder = $data['placeholder']
						?? $this->get_nested( $data, 'fieldItemPlaceholder', 'desktop', 'value' )
						?? null;
					if ( null !== $placeholder && '' !== $placeholder ) {
						$attrs['fieldItemPlaceholder']['desktop']['value'] = $placeholder;
					}
				}

				// Select options.
				if ( ! isset( $attrs['fieldItem']['advanced']['selectOptions']['desktop']['value'] ) ) {
					$select_options = $data['select_options']
						?? $this->get_nested( $data, 'fieldItem', 'advanced', 'selectOptions', 'desktop', 'value' )
						?? null;
					if ( null !== $select_options && is_array( $select_options ) && ! empty( $select_options ) ) {
						$attrs['fieldItem']['advanced']['selectOptions']['desktop']['value'] = $select_options;
					}
				}
				break;

			case 'divi/login':
			case 'divi/subscribe':
				if ( isset( $data['title'] ) ) {
					$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $data['title'] ] ];
				}
				if ( isset( $data['content'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
				}
				if ( isset( $data['button_text'] ) ) {
					$attrs['button']['innerContent'] = [ 'desktop' => [ 'value' => [ 'text' => $data['button_text'] ] ] ];
				}
				break;

			case 'divi/search':
				$attrs['search'] = [ 'advanced' => [
					'showButton'   => [ 'desktop' => [ 'value' => $data['show_button'] ?? 'on' ] ],
					'excludePages' => [ 'desktop' => [ 'value' => $data['exclude_pages'] ?? 'off' ] ],
					'excludePosts' => [ 'desktop' => [ 'value' => $data['exclude_posts'] ?? 'off' ] ],
				] ];
				break;
		}

		return [
			'attrs'      => $attrs,
			'inner'      => $inner_html,
			'inner_html' => $inner_html,
		];
	}
}
